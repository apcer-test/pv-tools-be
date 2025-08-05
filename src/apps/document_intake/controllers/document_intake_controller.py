from typing import Annotated, Any
import logging
from ulid import ULID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse

import constants
from apps.document_intake.schemas.request import DocumentUploadRequest
from apps.document_intake.schemas.response import DocumentExtractionResponse
from apps.document_intake.services.document_intake_service import DocumentIntakeService
from apps.ai_extraction.schemas.request import DocType
from apps.ai_extraction.services.audit_logger import AuditLogger
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/api/document-intake", tags=["Document Intake"])
logger = logging.getLogger(__name__)


@router.post(
    "/extract",
    status_code=status.HTTP_200_OK,
    name="Extract Document",
    description="Upload a PDF document for AI extraction",
    operation_id="extract_document"
)
async def extract_document_endpoint(
    service: Annotated[DocumentIntakeService, Depends()],
    audit_logger: Annotated[AuditLogger, Depends()],
    file: Annotated[UploadFile, File(..., description="PDF file to extract data from")],
    doc_type: Annotated[DocType, Form(..., description="Document type (CIOMS, IRMS, AER, LAB_REPORT, UNKNOWN)")],
) -> BaseResponse[dict[str, Any]]:
    """
    Upload and extract data from a PDF document using AI.
    
    This endpoint accepts a PDF file upload along with document type information
    and processes it through the AI extraction pipeline.
    
    Args:
        file: The PDF file to process
        doc_type: Type of document for appropriate extraction logic
        service: Document intake service dependency
        audit_logger: Audit logger for comprehensive logging
        
    Returns:
        BaseResponse[DocumentExtractionResponse]: Extraction results or error information
    """
    # Generate request ID for tracking
    request_id = ULID()
    
    try:
        # Log request start
        logger.info(f"Document extraction request received - RequestID: {request_id}, DocType: {doc_type}, File: {file.filename}")
        
        # Get file size for logging
        file_size = 0
        if hasattr(file, 'size'):
            file_size = file.size
        else:
            # Read file to get size if not available
            content = await file.read()
            file_size = len(content)
            # Reset file position for processing
            await file.seek(0)
        
        # Log request start with audit logger
        await audit_logger.log_request_start(
            request_id=request_id,
            doc_type=doc_type,
            file_name=file.filename or "unknown",
            file_size=file_size
        )
        
        # Process the document
        result = await service.process_document(
            file=file,
            doc_type=doc_type,
            request_id=request_id,
            audit_logger=audit_logger
        )
        
        # Log successful completion
        logger.info(f"Document extraction completed successfully - RequestID: {request_id}, Status: {result.status}")
        
        return BaseResponse(data=result)
        
    except Exception as e:
        # Log unexpected errors
        error_msg = f"Unexpected error in document extraction endpoint - RequestID: {request_id}, Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Log error with audit logger
        await audit_logger.log_error(
            request_id=request_id,
            error_code="CONTROLLER_ERROR",
            error_message=str(e),
            failed_at_step="controller"
        )
        
        # Return error response
        error_response = DocumentExtractionResponse(
            request_id=request_id,
            status="error",
            error_code="INTERNAL_ERROR",
            error_message="An unexpected error occurred during document processing",
            failed_at_step="controller"
        )
        
        return BaseResponse(data=error_response)
