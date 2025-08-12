from fastapi import APIRouter

from apps.roles.controllers.roles import router as roles_router

router = APIRouter()
router.include_router(roles_router)

__all__ = ["router"]
