"""Task distribution module for queuing long running
algorithm process
"""


from celery import Celery

celery = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

celery.conf.update(
    task_routes={
        "api.service.tasks.run_main_algorithm": {"queue": "algorithm_queue"}
    },
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_ignore_result=False,
    result_persistent=True,
    broker_connection_retry_on_startup=True
)

celery.autodiscover_tasks(['api.service'])
