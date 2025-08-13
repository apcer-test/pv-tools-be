from fastapi import APIRouter

from apps.user_type.controllers.user_type import router as user_type_router

router = APIRouter()
router.include_router(user_type_router)

__all__ = ["router"]
