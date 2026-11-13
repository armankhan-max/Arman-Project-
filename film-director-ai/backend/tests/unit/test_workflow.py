import time

import pytest

from fda.agents import HANDLERS
from fda.database import models as m
from fda.database.session import SessionLocal
from fda.orchestration import workflow

CALLS = []


def ok(ctx):
    CALLS.append(ctx.task.key)
    return {"summary": "ok", "state": {ctx.task.key: True}}


def spawner(ctx):
    CALLS.append(ctx.task.key)
    return {"spawn": [{"key": "child:%d" % i, "agent": "t_ok", "depends_on": ["parent"]} for i in range(3)]}


class Flaky(Exception):
    retryable = True


def flaky(ctx):
    CALLS.append(ctx.task.key)
    if ctx.task.attempts < 2:
        raise Flaky("transient")
    return {"summary": "recovered"}


def boom(ctx):
    raise ValueError("permanent")


@pytest.fixture(autouse=True)
def handlers(monkeypatch):
    CALLS.clear()
    HANDLERS["t_ok"], HANDLERS["t_spawn"], HANDLERS["t_flaky"], HANDLERS["t_boom"] = ok, spawner, flaky, boom
    monkeypatch.setattr(workflow, "submit", lambda tid, q="default": workflow.execute_task(tid))  # run inline, deterministic
    monkeypatch.setattr(workflow.time, "sleep", lambda s: None)
    yield


def wait(run_id):
    s = SessionLocal()
    try:
        return s.get(m.WorkflowRun, run_id)
    finally:
        s.close()


def test_dependencies_spawn_and_checkpoint(db, project):
    run = workflow.create_run(db, project.id, "test", [
        {"key": "a", "agent": "t_ok"}, {"key": "parent", "agent": "t_spawn", "depends_on": ["a"]},
        {"key": "after", "agent": "t_ok", "depends_on": ["child:*"]}])
    db.commit()
    workflow.dispatch(run.id)
    r = wait(run.id)
    assert r.status == "succeeded"
    assert CALLS.index("a") < CALLS.index("parent") < CALLS.index("after")
    assert all(CALLS.index("child:%d" % i) < CALLS.index("after") for i in range(3))
    assert r.state["a"] and r.state["after"]


def test_retry_then_success(db, project):
    run = workflow.create_run(db, project.id, "test", [{"key": "f", "agent": "t_flaky", "max_attempts": 3}])
    db.commit()
    workflow.dispatch(run.id)
    for _ in range(5):
        workflow.dispatch(run.id)
    r = wait(run.id)
    assert r.status == "succeeded" and CALLS.count("f") == 2


def test_failure_blocks_dependents_and_resume(db, project):
    run = workflow.create_run(db, project.id, "test", [{"key": "x", "agent": "t_boom", "max_attempts": 1}, {"key": "y", "agent": "t_ok", "depends_on": ["x"]}])
    db.commit()
    workflow.dispatch(run.id)
    r = wait(run.id)
    assert r.status == "failed" and "permanent" in r.error
    s = SessionLocal()
    y = s.query(m.WorkflowTask).filter_by(run_id=run.id, key="y").one()
    assert y.status == "cancelled"
    HANDLERS["t_boom"] = ok  # the problem is fixed → resume continues from the checkpoint
    workflow.resume(s, run.id)
    s.close()
    assert wait(run.id).status == "succeeded" and CALLS == ["x", "y"]


def test_cancel(db, project):
    run = workflow.create_run(db, project.id, "test", [{"key": "a", "agent": "t_ok"}])
    run.cancel_requested = True
    db.commit()
    workflow.dispatch(run.id)
    assert wait(run.id).status == "cancelled" and CALLS == []


def test_worker_crash_recovery(db, project, monkeypatch):
    run = workflow.create_run(db, project.id, "test", [{"key": "a", "agent": "t_ok"}])
    db.commit()
    t = db.query(m.WorkflowTask).filter_by(run_id=run.id).one()
    t.status = "running"  # simulate a worker that died mid-task
    run.status = "running"
    db.commit()
    workflow.recover_stale(0)
    assert wait(run.id).status == "succeeded" and CALLS == ["a"]
