from core.exceptions import BadRequestError


class AICBClientError(BadRequestError):
    """Custom exception for User already assigned error."""

    message = "Error in calling AICB API"
