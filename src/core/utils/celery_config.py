from celery import Celery

from config import settings

celery_app = Celery(
    "tasks", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(task_ignore_result=True, worker_prefetch_multiplier=1)

celery_app.conf.task_routes = {
    "core.utils.celery_worker.pooling_mail_box": "main-queue"
}
