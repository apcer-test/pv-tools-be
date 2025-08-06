import psutil
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.utils import logger

class MemoryUsageMiddleware(BaseHTTPMiddleware):
    """Middleware to log memory usage before and after each request"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get the request path
        path = request.url.path

        # Log memory before processing the request
        logger.info(
            f"Memory before {request.method} {path}: {psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB"
        )

        # Process the request
        response = await call_next(request)

        # # Log memory after processing the request
        logger.info(
            f"Memory after {request.method} {path}: {psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB"
        )

        return response
