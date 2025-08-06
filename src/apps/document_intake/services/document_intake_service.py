import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Annotated, Union

from fastapi import Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from apps.ai_extraction.schemas.request import DocType
from apps.ai_extraction.schemas.response import ExtractionError, ExtractionResult
from apps.ai_extraction.services.audit_logger import AuditLogger
from apps.ai_extraction.services.orchestrator import Orchestrator
from apps.document_intake.models.document_intake import (
    DocumentIntakeHistory,
    DocumentIntakeSource,
    DocumentIntakeStatus,
)
from apps.document_intake.schemas.response import DocumentExtractionResponse
from core.db import db_session


class DocumentIntakeService:
    """Service class for handling document intake and extraction"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]):
        """Initialize the DocumentIntakeService with a database session"""
        self.session = session
        self.orchestrator = Orchestrator(session=session)
        self.logger = logging.getLogger(__name__)

    async def create_intake_record(
        self,
        request_id: ULID,
        source: DocumentIntakeSource,
        file_path: str,
        file_name: str,
        doc_type: DocType,
        file_size: int = None,
        email_body: str = None,
        metadata: dict = None,
    ) -> DocumentIntakeHistory:
        """Create a new document intake record"""

        # Get doc_type_id from the database
        from apps.ai_extraction.models.doctype import DocTypeModel

        doc_type_obj = await self.session.scalar(
            select(DocTypeModel).where(DocTypeModel.code == doc_type)
        )

        if not doc_type_obj:
            raise ValueError(f"Document type {doc_type} not found")

        intake_record = DocumentIntakeHistory(
            request_id=str(request_id),
            source=source,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            doc_type_id=doc_type_obj.id,
            email_body=email_body,
            meta_data=metadata or {},
        )

        self.session.add(intake_record)
        await self.session.flush()  # Generate ID for foreign key references

        return intake_record

    async def update_intake_status(
        self,
        request_id: str,
        status: DocumentIntakeStatus,
        error_message: str = None,
        error_code: str = None,
        failed_at_step: str = None,
    ) -> DocumentIntakeHistory:
        """Update the status of a document intake record"""

        intake_record = await self.session.scalar(
            select(DocumentIntakeHistory).where(
                DocumentIntakeHistory.request_id == request_id
            )
        )

        if not intake_record:
            raise ValueError(
                f"Document intake record with request_id {request_id} not found"
            )

        intake_record.status = status

        if status == DocumentIntakeStatus.IN_PROGRESS:
            intake_record.processing_started_at = datetime.utcnow().isoformat()
        elif status in [DocumentIntakeStatus.COMPLETED, DocumentIntakeStatus.FAILED]:
            intake_record.processing_completed_at = datetime.utcnow().isoformat()

        if error_message:
            intake_record.error_message = error_message
        if error_code:
            intake_record.error_code = error_code
        if failed_at_step:
            intake_record.failed_at_step = failed_at_step

        return intake_record

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

        # Create intake record
        file_size = 0
        if hasattr(file, "size"):
            file_size = file.size
        else:
            content = await file.read()
            file_size = len(content)
            await file.seek(0)

        intake_record = await self.create_intake_record(
            request_id=request_id,
            source=DocumentIntakeSource.USER_UPLOAD,
            file_path=file.filename or "unknown",
            file_name=file.filename or "unknown",
            doc_type=doc_type,
            file_size=file_size,
        )

        # Update status to IN_PROGRESS
        await self.update_intake_status(
            str(request_id), DocumentIntakeStatus.IN_PROGRESS
        )

        # Update the audit logger to use the same session
        audit_logger.session = self.session

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

                # Update intake status to FAILED
                await self.update_intake_status(
                    str(request_id),
                    DocumentIntakeStatus.FAILED,
                    error_message=error_msg,
                    error_code="UNSUPPORTED_FILE_TYPE",
                    failed_at_step="file_validation",
                )

                # Log validation error with audit logger
                await audit_logger.log_error(
                    request_id=request_id,
                    error_code="UNSUPPORTED_FILE_TYPE",
                    error_message=error_msg,
                    failed_at_step="file_validation",
                    document_intake_id=intake_record.id,
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

                # Update intake status to FAILED
                await self.update_intake_status(
                    str(request_id),
                    DocumentIntakeStatus.FAILED,
                    error_message=error_msg,
                    error_code="FILE_CREATION_ERROR",
                    failed_at_step="file_creation",
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

            # Log request start with document intake ID
            await audit_logger.log_request_start(
                request_id=request_id,
                doc_type=doc_type,
                file_name=file.filename or "unknown",
                file_size=file_size,
                document_intake_id=intake_record.id,
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
                document_intake_id=intake_record.id,
            )

            # Convert result to response format
            if isinstance(result, ExtractionResult):
                await self.update_intake_status(
                    str(request_id), DocumentIntakeStatus.COMPLETED
                )
                self.logger.info(
                    f"AI extraction successful - RequestID: {request_id}, Fields: {len(result.data) if result.data else 0}"
                )

                return DocumentExtractionResponse(
                    request_id=request_id, status="success", data=result.data
                )
            elif isinstance(result, ExtractionError):
                # Update intake status to FAILED
                await self.update_intake_status(
                    str(request_id),
                    DocumentIntakeStatus.FAILED,
                    error_message=result.error_message,
                    error_code=result.error_code,
                    failed_at_step=result.failed_at_step,
                )

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

                # Update intake status to FAILED
                await self.update_intake_status(
                    str(request_id),
                    DocumentIntakeStatus.FAILED,
                    error_message=error_msg,
                    error_code="UNKNOWN_RESULT_TYPE",
                    failed_at_step="processing",
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

            # Update intake status to FAILED
            await self.update_intake_status(
                str(request_id),
                DocumentIntakeStatus.FAILED,
                error_message=error_msg,
                error_code="PROCESSING_ERROR",
                failed_at_step="processing",
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
