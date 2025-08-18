from fastapi import APIRouter

from apps.users.controllers.user import router as user_router

router = APIRouter()
router.include_router(user_router)

__all__ = ["router"]
