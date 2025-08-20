from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.models.user import LoginActivity
from apps.users.schemas.request import LoginActivityCreate


async def log_login_activity(db: AsyncSession, data: LoginActivityCreate):
    """
    Log a login activity.
    """
    log_entry = LoginActivity(
        user_id=data.user_id,
        client_id=data.client_id,
        status=data.status,
        activity=data.activity,
        reason=data.reason,
        ip_address=data.ip_address,
        timestamp=datetime.utcnow(),
    )
    db.add(log_entry)
    return log_entry
