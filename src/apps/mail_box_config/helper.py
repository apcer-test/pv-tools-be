import constants
from core.db import redis
from core.utils.celery_worker import celery_app


async def revoke_running_task(mail_box_config_id: str) -> None:
    """Revokes a running Celery task associated with the given bank ID."""
    running_task_id = await redis.get(mail_box_config_id)
    if running_task_id is not None:
        celery_app.control.revoke(
            running_task_id, terminate=True, signal=constants.SIGKILL
        )
