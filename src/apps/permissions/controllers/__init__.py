from fastapi import APIRouter

from apps.permissions.controllers.permissions import router as permissions_router

router = APIRouter()
router.include_router(permissions_router)

__all__ = ["router"]
