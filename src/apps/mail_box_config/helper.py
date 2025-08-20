from core.db import redis
from core.utils.celery_worker import celery_app


async def revoke_running_task(mail_box_config_id: str) -> None:
    """Revokes a running Celery task associated with the given bank ID."""
    running_task_id = await redis.get(mail_box_config_id)
    if running_task_id is not None:
        # Use SIGTERM instead of SIGKILL for Windows compatibility
        celery_app.control.revoke(running_task_id, terminate=True)
        # Clean up the Redis key
        await redis.delete(str(mail_box_config_id))


def mask_password(password: str | None) -> str | None:
    """Mask a password string, showing only the last 4 characters."""
    if not password:
        return None
    if len(password) <= 4:
        return "*" * len(password)
    return "*" * (len(password) - 4) + password[-4:]
