"""Persistent workflow engine.

A run is a DAG of tasks stored in PostgreSQL. Tasks become runnable when their dependencies succeed, are executed by
Celery workers (or a local thread pool), checkpoint their output into the run state, and retry with bounded attempts.
Handlers may spawn new tasks (e.g. one visual task per storyboard scene). Because every transition is written to the
database, a crashed worker or restarted server resumes from the last finished task."""
import fnmatch
import logging
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from fda.config import get_settings
from fda.database import models as m
from fda.database.session import SessionLocal, session_scope

log = logging.getLogger("fda.workflow")
DONE = ("succeeded", "skipped")
FINAL = ("succeeded", "failed", "skipped", "cancelled")
_pool = None
_pool_lock = threading.Lock()
_celery_ok = None


class Cancelled(RuntimeError):
    pass


class Retryable(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc)


# ------------------------------------------------------------------ events
def event(db, run_id, message, level="info", task_key=None, **data):
    db.add(m.WorkflowEvent(run_id=run_id, task_key=task_key, level=level, message=message[:2000], data=data))
    db.flush()


# ------------------------------------------------------------------ creation
def create_run(db, project_id, kind, tasks, state=None, plan=None):
    run = m.WorkflowRun(project_id=project_id, kind=kind, status="pending", state=state or {}, plan=plan or {})
    db.add(run)
    db.flush()
    add_tasks(db, run, tasks)
    event(db, run.id, "Workflow '%s' created with %d tasks" % (kind, len(tasks)))
    return run


def add_tasks(db, run, tasks):
    existing = {t.key for t in db.query(m.WorkflowTask).filter_by(run_id=run.id).all()}
    s = get_settings()
    for t in tasks:
        if t["key"] in existing:
            continue  # idempotent spawn
        db.add(m.WorkflowTask(run_id=run.id, key=t["key"], agent=t["agent"], queue=t.get("queue", "default"), depends_on=t.get("depends_on", []),
                              params=t.get("params", {}), max_attempts=t.get("max_attempts", s.max_retries + 1), timeout_s=t.get("timeout_s", 3600)))
    db.flush()


# ------------------------------------------------------------------ scheduling
def _deps_state(task, by_key):
    """'ready' | 'wait' | 'blocked'"""
    for d in task.depends_on or []:
        matches = [t for k, t in by_key.items() if fnmatch.fnmatchcase(k, d)] if any(c in d for c in "*?") else ([by_key[d]] if d in by_key else [])
        if not matches and not any(c in d for c in "*?"):
            return "blocked"
        for t in matches:
            if t.status in ("failed", "cancelled"):
                return "blocked"
            if t.status not in DONE:
                return "wait"
    return "ready"


def dispatch(run_id):
    """Queue every runnable task and settle the run status. Safe to call from anywhere, any number of times."""
    to_submit = []
    with session_scope() as db:
        run = db.execute(select(m.WorkflowRun).where(m.WorkflowRun.id == run_id).with_for_update()).scalar_one_or_none()
        if run is None or run.status in ("succeeded", "failed", "cancelled"):
            return
        tasks = db.query(m.WorkflowTask).filter_by(run_id=run_id).all()
        by_key = {t.key: t for t in tasks}
        if run.cancel_requested:
            for t in tasks:
                if t.status in ("pending", "queued"):
                    t.status = "cancelled"
            if not any(t.status == "running" for t in tasks):
                run.status, run.finished_at = "cancelled", now()
                event(db, run.id, "Workflow cancelled", "warn")
                _project_status(db, run)
            return
        if run.status == "pending":
            run.status, run.started_at = "running", now()
        running = sum(1 for t in tasks if t.status in ("queued", "running"))
        for t in tasks:
            if t.status != "pending":
                continue
            st = _deps_state(t, by_key)
            if st == "blocked":
                t.status, t.error = "cancelled", "A dependency failed"
                continue
            if st == "ready":
                if t.agent in HEAVY and running >= get_settings().max_concurrent_jobs * 4:
                    continue
                t.status = "queued"
                running += 1
                to_submit.append((str(t.id), t.queue))
        if all(t.status in FINAL for t in tasks):
            failed = [t for t in tasks if t.status in ("failed", "cancelled")]
            run.status = "failed" if failed else "succeeded"
            run.finished_at = now()
            if failed:
                run.error = "; ".join("%s: %s" % (t.key, (t.error or "")[:160]) for t in failed[:5])
            event(db, run.id, "Workflow %s" % run.status, "error" if failed else "info")
            _project_status(db, run)
    for tid, q in to_submit:
        submit(tid, q)


def _project_status(db, run):
    p = db.get(m.Project, run.project_id)
    if p is None:
        return
    if run.status == "succeeded":
        p.status = "ready"
    elif run.status == "failed":
        p.status = "needs_attention"
    elif run.status == "cancelled":
        p.status = "cancelled"


HEAVY = {"render", "visual", "blender"}


# ------------------------------------------------------------------ execution
def submit(task_id, queue="default"):
    if use_celery():
        from fda.workers.celery_app import execute_task as celery_task
        celery_task.apply_async(args=[task_id], queue=queue)
    else:
        global _pool
        with _pool_lock:
            if _pool is None:
                _pool = ThreadPoolExecutor(max_workers=max(2, get_settings().max_concurrent_jobs * 2), thread_name_prefix="fda-task")
        _pool.submit(execute_task, task_id)


def use_celery():
    global _celery_ok
    s = get_settings()
    if not s.use_celery:
        return False
    if _celery_ok is None or (isinstance(_celery_ok, float) and time.time() - _celery_ok > 30):
        try:
            import redis
            redis.Redis.from_url(s.redis_url, socket_connect_timeout=1).ping()
            from fda.workers.celery_app import app
            ok = bool(app.control.inspect(timeout=1.0).ping())
            _celery_ok = True if ok else time.time()
        except Exception:
            _celery_ok = time.time()
    return _celery_ok is True


class Ctx:
    """What a handler sees: db session, run, task, project, shared state and progress/event helpers."""

    def __init__(self, db, run, task):
        self.db, self.run, self.task = db, run, task
        self.project = db.get(m.Project, run.project_id)
        self.params = task.params or {}

    @property
    def state(self):
        return self.run.state or {}

    def progress(self, frac, msg=""):
        self.task.progress = max(0.0, min(1.0, float(frac)))
        if msg:
            self.task.message = msg[:500]
        self.task.heartbeat_at = now()
        self.db.commit()
        self.check_cancel()

    def log(self, msg, level="info", **data):
        event(self.db, self.run.id, msg, level, self.task.key, **data)
        self.db.commit()

    def check_cancel(self):
        self.db.refresh(self.run, ["cancel_requested"])
        if self.run.cancel_requested:
            raise Cancelled("Cancelled by owner")


def execute_task(task_id):
    from fda.agents import HANDLERS
    db = SessionLocal()
    run_id = None
    try:
        task = db.execute(select(m.WorkflowTask).where(m.WorkflowTask.id == task_id).with_for_update(skip_locked=True)).scalar_one_or_none()
        if task is None or task.status not in ("queued", "pending"):
            return
        run = db.get(m.WorkflowRun, task.run_id)
        run_id = run.id
        if run.cancel_requested:
            task.status = "cancelled"
            db.commit()
            return
        task.status, task.started_at, task.heartbeat_at = "running", now(), now()
        task.attempts += 1
        task.error = None
        db.commit()
        event(db, run.id, "Started (attempt %d)" % task.attempts, task_key=task.key)
        db.commit()
        handler = HANDLERS.get(task.agent)
        if handler is None:
            raise RuntimeError("No handler for agent '%s'" % task.agent)
        ctx = Ctx(db, run, task)
        t0 = time.time()
        out = handler(ctx) or {}
        spawn = out.pop("spawn", None)
        state_upd = out.pop("state", None)
        run = db.execute(select(m.WorkflowRun).where(m.WorkflowRun.id == run.id).with_for_update().execution_options(populate_existing=True)).scalar_one()
        if state_upd:
            st = dict(run.state or {})
            st.update(state_upd)
            run.state = st  # checkpoint
        if spawn:
            add_tasks(db, run, spawn)
        task.output = _jsonable(out)
        task.status = "skipped" if out.get("skipped") else "succeeded"
        task.progress, task.finished_at = 1.0, now()
        db.add(m.ToolRun(project_id=run.project_id, task_id=task.id, tool="agent:" + task.agent, args=_jsonable(task.params), result={"summary": str(out.get("summary", ""))[:500]},
                         ok=True, duration_ms=int((time.time() - t0) * 1000)))
        event(db, run.id, out.get("summary") or "Finished", task_key=task.key)
        db.commit()
    except Cancelled as e:
        db.rollback()
        _finish_fail(db, task_id, str(e), cancelled=True)
    except Exception as e:
        db.rollback()
        retry = getattr(e, "retryable", True) and not isinstance(e, (KeyError, TypeError)) and getattr(e, "code", None) not in ("budget", "not_configured")
        if type(e).__name__ == "BudgetError":
            retry = False
        log.warning("task %s failed: %s", task_id, e)
        _finish_fail(db, task_id, "%s: %s" % (type(e).__name__, e), retry=retry, tb=traceback.format_exc()[-2000:])
    finally:
        db.close()
        if run_id:
            dispatch(run_id)


def _finish_fail(db, task_id, msg, retry=False, cancelled=False, tb=None):
    task = db.get(m.WorkflowTask, task_id)
    if task is None:
        return
    if cancelled:
        task.status = "cancelled"
    elif retry and task.attempts < task.max_attempts:
        task.status = "pending"
        event(db, task.run_id, "Attempt %d failed, will retry: %s" % (task.attempts, msg[:300]), "warn", task.key)
        db.commit()
        time.sleep(min(30, 2 ** task.attempts))
        return
    else:
        task.status = "failed"
    task.error, task.finished_at = msg[:4000], now()
    event(db, task.run_id, ("Cancelled" if cancelled else "Failed: ") + ("" if cancelled else msg[:500]), "warn" if cancelled else "error", task.key, traceback=tb or "")
    db.commit()


def _jsonable(x):
    import json
    try:
        return json.loads(json.dumps(x, default=str))
    except Exception:
        return {}


# ------------------------------------------------------------------ control
def cancel(db, run_id):
    run = db.get(m.WorkflowRun, run_id)
    if run and run.status in ("pending", "running"):
        run.cancel_requested = True
        event(db, run.id, "Cancellation requested", "warn")
    db.commit()
    dispatch(run_id)


def resume(db, run_id):
    """Retry failed/cancelled tasks and everything downstream, keeping finished work."""
    run = db.get(m.WorkflowRun, run_id)
    if run is None:
        return None
    for t in db.query(m.WorkflowTask).filter_by(run_id=run_id).all():
        if t.status in ("failed", "cancelled", "running", "queued"):
            t.status, t.error, t.attempts = "pending", None, 0
    run.status, run.cancel_requested, run.error, run.finished_at = "running", False, None, None
    event(db, run.id, "Resumed from last checkpoint")
    p = db.get(m.Project, run.project_id)
    if p:
        p.status = "producing"
    db.commit()
    dispatch(run_id)
    return run


def recover_stale(max_age_s=None):
    """Tasks whose worker died (no heartbeat) go back to pending; called at startup and periodically."""
    with session_scope() as db:
        cutoff = now() - timedelta(seconds=max_age_s or 900)
        runs = set()
        for t in db.query(m.WorkflowTask).filter(m.WorkflowTask.status.in_(["running", "queued"])).all():
            hb = t.heartbeat_at or t.started_at or t.updated_at
            if max_age_s == 0 or hb is None or hb < cutoff:
                t.status = "pending"
                event(db, t.run_id, "Recovered after worker loss; re-queued", "warn", t.key)
                runs.add(t.run_id)
        active = db.query(m.WorkflowRun.id).filter(m.WorkflowRun.status.in_(["pending", "running"])).all()
        runs |= {r[0] for r in active}
    for r in runs:
        dispatch(r)
    return len(runs)
