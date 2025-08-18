from fastapi import APIRouter

from apps.clients.controllers.clients import router as clients_router

router = APIRouter()
router.include_router(clients_router)

__all__ = ["router"]
