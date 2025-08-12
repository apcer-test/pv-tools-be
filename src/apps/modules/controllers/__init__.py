from fastapi import APIRouter

from apps.modules.controllers.modules import router as module_router

router = APIRouter()
router.include_router(module_router)

__all__ = ["router"]
