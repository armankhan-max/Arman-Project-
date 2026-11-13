"""Celery application. Queues: default, research, transcription, visual, blender, audio, render, qc.
Start workers e.g.:  celery -A fda.workers.celery_app worker -Q default,research,transcription,visual,audio,qc -c 4
                      celery -A fda.workers.celery_app worker -Q render,blender -c 1"""
from celery import Celery
from celery.signals import worker_ready

from fda.config import get_settings

s = get_settings()
app = Celery("fda", broker=s.redis_url, backend=s.redis_url)
app.conf.update(task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1, task_default_queue="default",
                broker_connection_retry_on_startup=True, task_track_started=True, result_expires=3600,
                beat_schedule={"recover-stale": {"task": "fda.recover", "schedule": 300.0}, "retention": {"task": "fda.retention", "schedule": 6 * 3600.0}})


@app.task(name="fda.execute_task", bind=True)
def execute_task(self, task_id):
    from fda.orchestration.workflow import execute_task as run
    run(task_id)


@app.task(name="fda.recover")
def recover():
    from fda.orchestration.workflow import recover_stale
    return recover_stale()


@app.task(name="fda.retention")
def retention():
    from fda.services.retention import cleanup
    return cleanup()


@worker_ready.connect
def _on_ready(**_):
    from fda.orchestration.workflow import recover_stale
    try:
        recover_stale()
    except Exception:
        pass
