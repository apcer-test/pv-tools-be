import logging
import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from apps.ai_extraction.schemas.request import DocType
from apps.ai_extraction.schemas.response import ExtractionError, ExtractionResult
from apps.ai_extraction.services.audit_logger import AuditLogger
from apps.ai_extraction.services.orchestrator import Orchestrator
from apps.document_intake.schemas.response import DocumentExtractionResponse
from core.db import db_session


class DocumentIntakeService:
    """Service class for handling document intake and extraction"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]):
        """Initialize the DocumentIntakeService with a database session"""
        self.session = session
        self.orchestrator = Orchestrator(session=session)
        self.logger = logging.getLogger(__name__)

    async def process_document(
        self,
        file: UploadFile,
        doc_type: DocType,
        request_id: ULID,
        audit_logger: AuditLogger,
    ) -> DocumentExtractionResponse:
        """
        Process an uploaded document for AI extraction.

        Args:
            file: The uploaded file (PDF)
            doc_type: Type of document for extraction
            request_id: Request correlation ID for tracking
            audit_logger: Audit logger for comprehensive logging

        Returns:
            DocumentExtractionResponse: The extraction result
        """
        temp_file_path = None

        try:
            # Log file validation start
            self.logger.info(
                f"Starting file validation - RequestID: {request_id}, File: {file.filename}"
            )

            # Get file extension and validate
            file_extension = Path(file.filename).suffix.lower()
            supported_extensions = {".pdf"}  # will take this from constants

            if file_extension not in supported_extensions:
                error_msg = f"Unsupported file type: {file_extension}"
                self.logger.error(
                    f"File validation failed - RequestID: {request_id}, Error: {error_msg}"
                )

                # Log validation error with audit logger
                await audit_logger.log_error(
                    request_id=request_id,
                    error_code="UNSUPPORTED_FILE_TYPE",
                    error_message=error_msg,
                    failed_at_step="file_validation",
                )

                return DocumentExtractionResponse(
                    request_id=request_id,
                    status="error",
                    error_code="UNSUPPORTED_FILE_TYPE",
                    error_message=error_msg,
                    failed_at_step="file_validation",
                )

            # Log preprocessing start
            self.logger.info(
                f"Starting preprocessing - RequestID: {request_id}, File: {file.filename}"
            )
            await audit_logger.log_preprocessing_start(
                request_id=request_id, file_path=str(file.filename), doc_type=doc_type
            )

            # Create temporary file to store uploaded content
            try:
                # Create temporary file with the original extension
                with tempfile.NamedTemporaryFile(
                    suffix=file_extension, delete=False
                ) as temp_file:
                    temp_file_path = Path(temp_file.name)

                    # Write uploaded content to temporary file
                    content = await file.read()
                    temp_file.write(content)

                    # Log file creation
                    self.logger.info(
                        f"Temporary file created - RequestID: {request_id}, Path: {temp_file_path}, Size: {len(content)} bytes"
                    )

                # Log preprocessing completion
                await audit_logger.log_preprocessing_complete(
                    request_id=request_id,
                    file_type=file_extension.lstrip("."),
                    doc_type=doc_type,
                    page_count=None,  # Could be extracted from PDF
                    word_count=None,  # Could be extracted from PDF
                )

                self.logger.info(f"Preprocessing completed - RequestID: {request_id}")

            except Exception as e:
                error_msg = f"Failed to create temporary file: {str(e)}"
                self.logger.error(
                    f"File creation failed - RequestID: {request_id}, Error: {error_msg}"
                )

                await audit_logger.log_preprocessing_error(
                    request_id=request_id, error_message=error_msg, doc_type=doc_type
                )

                return DocumentExtractionResponse(
                    request_id=request_id,
                    status="error",
                    error_code="FILE_CREATION_ERROR",
                    error_message=error_msg,
                    failed_at_step="file_creation",
                )

            # Call the AI extraction service
            self.logger.info(
                f"Starting AI extraction - RequestID: {request_id}, DocType: {doc_type}"
            )

            result = await self.orchestrator.extract_document(
                request_id=request_id,
                file_path=temp_file_path,
                doc_type=doc_type,
                audit_logger=audit_logger,
            )

            # Convert result to response format
            if isinstance(result, ExtractionResult):
                self.logger.info(
                    f"AI extraction successful - RequestID: {request_id}, Fields: {len(result.data) if result.data else 0}"
                )

                return DocumentExtractionResponse(
                    request_id=request_id, status="success", data=result.data
                )
            elif isinstance(result, ExtractionError):
                self.logger.error(
                    f"AI extraction failed - RequestID: {request_id}, Error: {result.error_message}"
                )

                return DocumentExtractionResponse(
                    request_id=request_id,
                    status="error",
                    error_code=result.error_code,
                    error_message=result.error_message,
                    failed_at_step=result.failed_at_step,
                )
            else:
                error_msg = "Unexpected result type from extraction service"
                self.logger.error(
                    f"Unexpected result type - RequestID: {request_id}, Type: {type(result)}"
                )

                return DocumentExtractionResponse(
                    request_id=request_id,
                    status="error",
                    error_code="UNKNOWN_RESULT_TYPE",
                    error_message=error_msg,
                    failed_at_step="processing",
                )

        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.logger.error(
                f"Document processing failed - RequestID: {request_id}, Error: {error_msg}",
                exc_info=True,
            )

            # Log error with audit logger
            await audit_logger.log_error(
                request_id=request_id,
                error_code="PROCESSING_ERROR",
                error_message=error_msg,
                failed_at_step="processing",
            )

            return DocumentExtractionResponse(
                request_id=request_id,
                status="error",
                error_code="PROCESSING_ERROR",
                error_message=error_msg,
                failed_at_step="processing",
            )
        finally:
            # Clean up temporary file
            if temp_file_path and temp_file_path.exists():
                try:
                    os.unlink(temp_file_path)
                    self.logger.info(
                        f"Temporary file cleaned up - RequestID: {request_id}, Path: {temp_file_path}"
                    )
                except Exception as cleanup_error:
                    self.logger.warning(
                        f"Failed to cleanup temporary file - RequestID: {request_id}, Path: {temp_file_path}, Error: {str(cleanup_error)}"
                    )
