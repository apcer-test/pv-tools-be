from apps.ai_extraction.controllers.doctype import router as doctype_router
from apps.ai_extraction.controllers.extraction_agent import (
    router as extraction_agent_router,
)
from apps.ai_extraction.controllers.llm import router as llm_router
from apps.ai_extraction.controllers.prompt_registry import (
    router as prompt_registry_router,
)

__all__ = [
    "extraction_agent_router",
    "prompt_registry_router",
    "doctype_router",
    "llm_router",
]
