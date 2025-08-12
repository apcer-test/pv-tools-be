from fastapi import APIRouter

from apps.user_types.controllers.user_type import router as usertype_router

router = APIRouter()
router.include_router(usertype_router)

__all__ = ["router"]
