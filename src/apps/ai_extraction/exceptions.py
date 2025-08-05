"""Custom exceptions for AI extraction module"""


class   AIExtractionBaseException(Exception):
    """Base exception for all AI extraction errors"""
    pass


class PreProcessError(AIExtractionBaseException):
    """Raised when document preprocessing fails"""
    pass


class TemplateNotFoundError(AIExtractionBaseException):
    """Raised when no active template is found for a document type"""
    pass


class TemplateRenderError(AIExtractionBaseException):
    """Raised when template rendering fails"""
    pass


class ProviderError(AIExtractionBaseException):
    """Raised when LLM provider calls fail"""
    
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"{error_code}: {message}")


class ValidationError(AIExtractionBaseException):
    """Raised when JSON schema validation fails"""
    pass


class ExtractionFailedError(AIExtractionBaseException):
    """Raised when the entire extraction pipeline fails"""
    pass


class ChainExhaustedError(AIExtractionBaseException):
    """Raised when all fallback models fail"""
    pass 