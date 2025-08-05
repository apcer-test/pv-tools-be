"""Audit Logger - Comprehensive audit logging for extraction operations"""
from sqlalchemy import select
from typing import Annotated, Dict, Any, Optional
from ulid import ULID
from datetime import datetime
from decimal import Decimal
import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import db_session
from apps.ai_extraction.models.extraction_audit import ExtractionAuditModel
from apps.ai_extraction.schemas.request import DocType
from apps.ai_extraction.schemas.response import ExtractionDataResult, ExtractionError
from apps.ai_extraction.models.doctype import DocTypeModel
from apps.ai_extraction.models.llm import LLMModel, LLMCredentialModel
from apps.ai_extraction.models.fallback import FallbackStepModel


class AuditLogger:
    """Service for logging extraction operations and maintaining audit trails."""
    
    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Initialize with database session.
        
        Args:
            session: Database session for audit logging
        """
        self.session = session
        self.logger = logging.getLogger(__name__)
        # Cache for ID lookups within the same request
        self._id_cache = {}
        # Store document_intake_id for use across methods
        self.current_document_intake_id = None

    async def log_request_start(self,
        request_id: ULID,
        doc_type: DocType,
        file_name: str,
        file_size: int,
        external_id: Optional[str] = None,
        document_intake_id: str = None
    ) -> None:
        """Log the start of a new extraction request.
        
        Args:
            request_id: Request correlation ID
            doc_type: Document type being processed
            file_name: Name of uploaded file
            file_size: Size of uploaded file in bytes
            external_id: Optional external correlation ID
            document_intake_id: Document intake history ID for retry functionality
        """
        self.current_document_intake_id = document_intake_id
        self.logger.info(f"Extraction request started - RequestID: {request_id}, DocType: {doc_type}, File: {file_name}, Size: {file_size}")
        
        # Log to database
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=external_id,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=None,
            chain_id=None,
            template_id=None,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="REQUEST_STARTED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=None,
            step_id=None,
            document_intake_id=document_intake_id
        )

    async def log_preprocessing_start(self,
        request_id: ULID,
        file_path: str,
        doc_type: DocType
    ) -> None:
        """Log the start of preprocessing phase.
        
        Args:
            request_id: Request correlation ID
            file_path: Path to file being processed
            doc_type: Document type being processed
        """
        self.logger.info(f"Preprocessing started - RequestID: {request_id}, File: {file_path}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=None,
            chain_id=None,
            template_id=None,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="PREPROCESSING_STARTED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=None,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_preprocessing_complete(self,
        request_id: ULID,
        file_type: str,
        doc_type: DocType,
        page_count: Optional[int] = None,
        word_count: Optional[int] = None
    ) -> None:
        """Log the completion of preprocessing phase.
        
        Args:
            request_id: Request correlation ID
            file_type: Type of file processed
            doc_type: Document type being processed
            page_count: Number of pages (for PDFs)
            word_count: Number of words extracted
        """
        self.logger.info(f"Preprocessing completed - RequestID: {request_id}, Type: {file_type}, Pages: {page_count}, Words: {word_count}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=None,
            chain_id=None,
            template_id=None,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="PREPROCESSING_COMPLETED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=None,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_preprocessing_error(self,
        request_id: ULID,
        error_message: str,
        doc_type: DocType
    ) -> None:
        """Log preprocessing error.
        
        Args:
            request_id: Request correlation ID
            error_message: Error description
            doc_type: Document type being processed
        """
        self.logger.error(f"Preprocessing failed - RequestID: {request_id}, Error: {error_message}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=None,
            chain_id=None,
            template_id=None,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="PREPROCESSING_FAILED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=error_message,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_agent_start(self,
        request_id: ULID,
        agent_code: str,
        agent_id: ULID,
        template_id: ULID,
        doc_type: DocType
    ) -> None:
        """Log the start of agent execution.
        
        Args:
            request_id: Request correlation ID
            agent_code: Code of the extraction agent
            agent_id: Agent ULID
            template_id: Template ULID being used
            doc_type: Document type being processed
        """
        self.logger.info(f"Agent execution started - RequestID: {request_id}, Agent: {agent_code}, Template: {template_id}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id,
            chain_id=None,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="AGENT_STARTED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=None,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_llm_call_start(self,
        request_id: ULID,
        step: FallbackStepModel,
        agent_code: str,
        model_name: str,
        provider: str,
        doc_type: DocType,
        agent_id: Optional[ULID] = None,
        template_id: Optional[ULID] = None
    ) -> None:
        """Log the start of an LLM call.
        
        Args:
            request_id: Request correlation ID
            step: Fallback step being executed
            agent_code: Code of the extraction agent
            model_name: Name of the LLM model
            provider: LLM provider name
            doc_type: Document type being processed
            agent_id: Agent ULID
            template_id: Template ULID
        """
        self.logger.info(f"LLM call started - RequestID: {request_id}, Agent: {agent_code}, Model: {model_name}, Provider: {provider}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id or await self._get_agent_id(agent_code),
            chain_id=step.chain_id,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=step.model_id,
            credential_id=step.llm_credential_id,
            status="LLM_CALL_STARTED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=None,
            step_id=step.id,
            document_intake_id=self.current_document_intake_id
        )

    async def log_llm_call_success(self,
        request_id: ULID,
        step: FallbackStepModel,
        agent_code: str,
        model_name: str,
        provider: str,
        tokens_prompt: int,
        tokens_completion: int,
        cost_usd: Decimal,
        latency_ms: int,
        doc_type: DocType,
        agent_id: Optional[ULID] = None,
        template_id: Optional[ULID] = None
    ) -> None:
        """Log successful LLM call.
        
        Args:
            request_id: Request correlation ID
            step: Fallback step that was executed
            agent_code: Code of the extraction agent
            model_name: Name of the LLM model
            provider: LLM provider name
            tokens_prompt: Number of prompt tokens used
            tokens_completion: Number of completion tokens generated
            cost_usd: Cost of the call in USD
            latency_ms: Response latency in milliseconds
            doc_type: Document type being processed
            agent_id: Agent ULID
            template_id: Template ULID
        """
        self.logger.info(f"LLM call successful - RequestID: {request_id}, Agent: {agent_code}, Model: {model_name}, Tokens: {tokens_prompt}/{tokens_completion}, Cost: ${cost_usd}, Latency: {latency_ms}ms")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id or await self._get_agent_id(agent_code),
            chain_id=step.chain_id,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=step.model_id,
            credential_id=step.llm_credential_id,
            status="LLM_CALL_SUCCESS",
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            error_message=None,
            step_id=step.id,
            document_intake_id=self.current_document_intake_id
        )

    async def log_llm_call_failed(self,
        request_id: ULID,
        step: FallbackStepModel,
        agent_code: str,
        model_name: str,
        provider: str,
        error_message: str,
        doc_type: DocType,
        agent_id: Optional[ULID] = None,
        template_id: Optional[ULID] = None,
        latency_ms: int = 0
    ) -> None:
        """Log failed LLM call.
        
        Args:
            request_id: Request correlation ID
            step: Fallback step that failed
            agent_code: Code of the extraction agent
            model_name: Name of the LLM model
            provider: LLM provider name
            error_message: Error description
            doc_type: Document type being processed
            agent_id: Agent ULID
            template_id: Template ULID
            latency_ms: Response latency in milliseconds (if any)
        """
        self.logger.error(f"LLM call failed - RequestID: {request_id}, Agent: {agent_code}, Model: {model_name}, Error: {error_message}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id or await self._get_agent_id(agent_code),
            chain_id=step.chain_id,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=step.model_id,
            credential_id=step.llm_credential_id,
            status="LLM_CALL_FAILED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=latency_ms,
            error_message=error_message,
            step_id=step.id,
            document_intake_id=self.current_document_intake_id
        )

    async def log_validation_start(self,
        request_id: ULID,
        agent_code: str,
        doc_type: DocType,
        agent_id: ULID,
        template_id: ULID
    ) -> None:
        """Log the start of response validation.
        
        Args:
            request_id: Request correlation ID
            agent_code: Code of the extraction agent
            doc_type: Document type for validation
            agent_id: Agent ULID
            template_id: Template ULID
        """
        self.logger.info(f"Validation started - RequestID: {request_id}, Agent: {agent_code}, DocType: {doc_type}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id,
            chain_id=None,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="VALIDATION_STARTED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=None,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_validation_success(self,
        request_id: ULID,
        agent_code: str,
        doc_type: DocType,
        field_count: int,
        agent_id: ULID,
        template_id: ULID
    ) -> None:
        """Log successful validation.
        
        Args:
            request_id: Request correlation ID
            agent_code: Code of the extraction agent
            doc_type: Document type validated
            field_count: Number of fields extracted
            agent_id: Agent ULID
            template_id: Template ULID
        """
        self.logger.info(f"Validation successful - RequestID: {request_id}, Agent: {agent_code}, DocType: {doc_type}, Fields: {field_count}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id,
            chain_id=None,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="VALIDATION_SUCCESS",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=None,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_validation_failed(self,
        request_id: ULID,
        agent_code: str,
        doc_type: DocType,
        error_message: str,
        agent_id: ULID,
        template_id: ULID
    ) -> None:
        """Log validation failure.
        
        Args:
            request_id: Request correlation ID
            agent_code: Code of the extraction agent
            doc_type: Document type that failed validation
            error_message: Validation error description
            agent_id: Agent ULID
            template_id: Template ULID
        """
        self.logger.error(f"Validation failed - RequestID: {request_id}, Agent: {agent_code}, DocType: {doc_type}, Error: {error_message}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id,
            chain_id=None,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="VALIDATION_FAILED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=error_message,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_agent_complete(self,
        request_id: ULID,
        agent_code: str,
        agent_id: ULID,
        doc_type: DocType,
        field_count: int,
        total_cost: Decimal,
        total_latency: int,
        template_id: ULID
    ) -> None:
        """Log successful agent completion.
        
        Args:
            request_id: Request correlation ID
            agent_code: Code of the extraction agent
            agent_id: Agent ULID
            doc_type: Document type processed
            field_count: Number of fields extracted
            total_cost: Total cost for this agent
            total_latency: Total latency for this agent
            template_id: Template ULID
        """
        self.logger.info(f"Agent completed - RequestID: {request_id}, Agent: {agent_code}, Fields: {field_count}, Cost: ${total_cost}, Latency: {total_latency}ms")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id,
            chain_id=None,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="AGENT_COMPLETED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=total_cost,
            latency_ms=total_latency,
            error_message=None,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_agent_failed(self,
        request_id: ULID,
        agent_code: str,
        agent_id: ULID,
        doc_type: DocType,
        error_message: str,
        template_id: ULID
    ) -> None:
        """Log agent failure.
        
        Args:
            request_id: Request correlation ID
            agent_code: Code of the extraction agent
            agent_id: Agent ULID
            doc_type: Document type that failed
            error_message: Error description
            template_id: Template ULID
        """
        self.logger.error(f"Agent failed - RequestID: {request_id}, Agent: {agent_code}, Error: {error_message}")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id,
            chain_id=None,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="AGENT_FAILED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=error_message,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def log_extraction_complete(self,
        request_id: ULID,
        doc_type: DocType,
        total_agents: int,
        successful_agents: int,
        total_cost: Decimal,
        total_latency: int,
        total_fields: int,
        template_id: ULID | None = None
    ) -> None:
        """Log successful extraction completion.
        
        Args:
            request_id: Request correlation ID
            doc_type: Document type processed
            total_agents: Total number of agents attempted
            successful_agents: Number of successful agents
            total_cost: Total cost across all agents
            total_latency: Total latency across all agents
            total_fields: Total number of fields extracted
            template_id: Template ULID
        """
        self.logger.info(f"Extraction completed - RequestID: {request_id}, DocType: {doc_type}, Agents: {successful_agents}/{total_agents}, Fields: {total_fields}, Cost: ${total_cost}, Latency: {total_latency}ms")
        
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=None,
            chain_id=None,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="EXTRACTION_COMPLETED",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=total_cost,
            latency_ms=total_latency,
            error_message=None,
            step_id=None,
            document_intake_id=self.current_document_intake_id
        )

    async def process_outcome(self,
        outcome: Dict[str, Any],
        request_id: ULID,
        template_id: ULID,
        doc_type: DocType,
        agent_code: Optional[str] = None,
        agent_id: Optional[ULID] = None,
        chain_id: Optional[ULID] = None,
        step_id: Optional[ULID] = None
    ) -> ExtractionDataResult:
        """Process successful outcome and create audit record.
        
        Args:
            outcome: Extraction outcome with model results
            request_id: Request correlation ID
            template_id: Template used for extraction
            doc_type: Document type processed
            agent_code: Optional agent code for agent-specific logging
            agent_id: Optional agent ULID
            chain_id: Optional chain ULID
            step_id: Optional step ULID
            
        Returns:
            ExtractionDataResult for client response
        """
        # Insert audit record
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type),
            agent_id=agent_id,
            chain_id=chain_id,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=await self._get_model_id(outcome.get("model_used")),
            credential_id=outcome.get("credential_id"),
            status="PROCESS OUTCOME SUCCESS",
            tokens_prompt=outcome.get("tokens_prompt"),
            tokens_completion=outcome.get("tokens_completion"),
            cost_usd=outcome.get("cost_usd"),
            latency_ms=outcome.get("latency_ms"),
            error_message=None,
            step_id=step_id,
            document_intake_id=self.current_document_intake_id
        )
        
        # Return success response
        return ExtractionDataResult(
            request_id=request_id,
            doc_type=doc_type,
            data=outcome,
            model_used=outcome.get("model_used"),
            tokens_prompt=outcome.get("tokens_prompt"),
            tokens_completion=outcome.get("tokens_completion"),
            cost_usd=outcome.get("cost_usd"),
            latency_ms=outcome.get("latency_ms"),
            template_id=template_id,
            agent_code=agent_code,
            extracted_at=datetime.utcnow()
        )

    async def log_error(self,
        request_id: ULID,
        error_code: str,
        error_message: str,
        failed_at_step: str | None = None,
        retry_count: int | None = None,
        agent_code: Optional[str] = None,
        doc_type: Optional[DocType] = None,
        agent_id: Optional[ULID] = None,
        template_id: Optional[ULID] = None,
        chain_id: Optional[ULID] = None,
        step_id: Optional[ULID] = None
    ) -> ExtractionError:
        """Log extraction error and return error response.
        
        Args:
            request_id: Request correlation ID
            error_code: Error classification code
            error_message: Error description
            failed_at_step: Pipeline step where failure occurred
            retry_count: Number of retries attempted
            agent_code: Optional agent code for agent-specific logging
            doc_type: Optional document type
            agent_id: Optional agent ULID
            template_id: Optional template ULID
            chain_id: Optional chain ULID
            step_id: Optional step ULID
            
        Returns:
            ExtractionError for client response
        """
        self.logger.error(f"Extraction error - RequestID: {request_id}, Code: {error_code}, Step: {failed_at_step}, Error: {error_message}")
        
        # Create error response
        error_response = ExtractionError(
            request_id=request_id,
            error_code=error_code,
            error_message=error_message,
            failed_at_step=failed_at_step,
            retry_count=retry_count,
            agent_code=agent_code,
            created_at=datetime.utcnow()
        )
        
        # Log error to audit table
        await self._insert_extraction_audit(
            request_id=request_id,
            external_id=None,
            doc_type_id=await self._get_doc_type_id(doc_type) if doc_type else None,
            agent_id=agent_id,
            chain_id=chain_id,
            template_id=template_id,
            step_seq_no=await self._get_next_sequence_number(request_id),
            model_id=None,
            credential_id=None,
            status="EXTRACTION_ERROR",
            tokens_prompt=0,
            tokens_completion=0,
            cost_usd=Decimal('0.00'),
            latency_ms=0,
            error_message=error_message,
            step_id=step_id,
            document_intake_id=self.current_document_intake_id
        )
        
        return error_response

    async def _insert_extraction_audit(self,
        request_id: ULID,
        external_id: str | None,
        doc_type_id: ULID | None,
        agent_id: ULID | None,
        chain_id: ULID | None,
        template_id: ULID | None,
        step_seq_no: int,
        model_id: ULID | None,
        credential_id: ULID | None,
        status: str,
        tokens_prompt: int,
        tokens_completion: int,
        cost_usd: Decimal,
        latency_ms: int,
        error_message: str | None = None,
        step_id: ULID | None = None,
        document_intake_id: str | None = None
    ) -> None:
        """Insert audit record into database.
        
        Args:
            request_id: Request correlation ID
            external_id: External correlation ID
            doc_type_id: Document type ULID
            agent_id: Agent ULID
            chain_id: Fallback chain ULID
            template_id: Template ULID
            step_seq_no: Step sequence number
            model_id: Model ULID
            credential_id: Credential ULID
            status: Operation status
            tokens_prompt: Prompt tokens used
            tokens_completion: Completion tokens generated
            cost_usd: Cost in USD
            latency_ms: Response latency
            error_message: Error message if failed
            step_id: Fallback step ULID
            document_intake_id: Document intake history ID for retry functionality
        """
        try:
            audit_record = ExtractionAuditModel(
                request_id=str(request_id),
                external_id=external_id,
                doc_type_id=doc_type_id,
                agent_id=agent_id,
                chain_id=chain_id,
                template_id=template_id,
                step_seq_no=step_seq_no,
                model_id=model_id,
                credential_id=credential_id,
                status=status,
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_completion,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                error_message=error_message,
                step_id=step_id,
                document_intake_id=document_intake_id
            )
            
            self.session.add(audit_record)
            
        except Exception as e:
            self.logger.error(f"Failed to insert audit record: {str(e)}")

    async def _get_doc_type_id(self, doc_type: DocType) -> ULID | None:
        """Get doc type ULID from code.
        
        Args:
            doc_type: Document type code
            
        Returns:
            Document type ULID or None if not found
        """
        cache_key = f"doc_type_{doc_type}"
        if cache_key in self._id_cache:
            return self._id_cache[cache_key]
            
        try:
            doc_type_obj = await self.session.scalar(select(DocTypeModel).where(DocTypeModel.code == doc_type))
            result = doc_type_obj.id if doc_type_obj else None
            self._id_cache[cache_key] = result
            return result
        except Exception as e:
            self.logger.error(f"Failed to get doc type ID for {doc_type}: {str(e)}")
            return None

    async def _get_model_id(self, model_name: str) -> ULID | None:
        """Get model ULID from name.
        
        Args:
            model_name: Model name
            
        Returns:
            Model ULID or None if not found
        """
        if not model_name:
            return None
            
        cache_key = f"model_{model_name}"
        if cache_key in self._id_cache:
            return self._id_cache[cache_key]
            
        try:
            model_obj = await self.session.scalar(select(LLMModel).where(LLMModel.name == model_name))
            result = model_obj.id if model_obj else None
            self._id_cache[cache_key] = result
            return result
        except Exception as e:
            self.logger.error(f"Failed to get model ID for {model_name}: {str(e)}")
            return None

    async def _get_agent_id(self, agent_code: str) -> ULID | None:
        """Get agent ULID from code.
        
        Args:
            agent_code: Agent code
            
        Returns:
            Agent ULID or None if not found
        """
        cache_key = f"agent_{agent_code}"
        if cache_key in self._id_cache:
            return self._id_cache[cache_key]
            
        try:
            from apps.ai_extraction.models.llm import ExtractionAgentModel
            agent_obj = await self.session.scalar(select(ExtractionAgentModel).where(ExtractionAgentModel.code == agent_code))
            result = agent_obj.id if agent_obj else None
            self._id_cache[cache_key] = result
            return result
        except Exception as e:
            self.logger.error(f"Failed to get agent ID for {agent_code}: {str(e)}")
            return None

    async def _get_template_id(self, template_code: str) -> ULID | None:
        """Get template ULID from code.
        
        Args:
            template_code: Template code
            
        Returns:
            Template ULID or None if not found
        """
        try:
            from apps.ai_extraction.models.prompt_template import PromptTemplateModel
            template_obj = await self.session.scalar(select(PromptTemplateModel).where(PromptTemplateModel.code == template_code))
            return template_obj.id if template_obj else None
        except Exception as e:
            self.logger.error(f"Failed to get template ID for {template_code}: {str(e)}")
            return None

    async def _get_credential_id(self, credential_name: str) -> ULID | None:
        """Get credential ULID from name.
        
        Args:
            credential_name: Credential name
            
        Returns:
            Credential ULID or None if not found
        """
        try:
            credential_obj = await self.session.scalar(select(LLMCredentialModel).where(LLMCredentialModel.name == credential_name))
            return credential_obj.id if credential_obj else None
        except Exception as e:
            self.logger.error(f"Failed to get credential ID for {credential_name}: {str(e)}")
            return None

    async def _get_next_sequence_number(self, request_id: ULID) -> int:
        """Get next sequence number for a request.
        
        Args:
            request_id: Request correlation ID
            
        Returns:
            Next sequence number
        """
        try:
            result = await self.session.scalar(
                select(ExtractionAuditModel.step_seq_no)
                .where(ExtractionAuditModel.request_id == str(request_id))
                .order_by(ExtractionAuditModel.step_seq_no.desc())
                .limit(1)
            )
            return (result or 0) + 1
        except Exception as e:
            self.logger.error(f"Failed to get next sequence number for {request_id}: {str(e)}")
            return 1

    async def get_extraction_stats(self,
        doc_type: DocType | None = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get extraction statistics.
        
        Args:
            doc_type: Optional document type filter
            days: Number of days to look back
            
        Returns:
            Dictionary with extraction statistics
        """
        # TODO: Implement statistics queries
        return {
            "total_extractions": 0,
            "success_rate": 0.0,
            "average_cost_usd": 0.0,
            "average_latency_ms": 0,
            "top_models": [],
            "error_breakdown": {}
        }

    async def get_cost_breakdown(self,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> Dict[str, Any]:
        """Get cost breakdown by model, provider, etc.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with cost breakdown
        """
        # TODO: Implement cost analysis queries
        return {
            "total_cost_usd": 0.0,
            "cost_by_provider": {},
            "cost_by_model": {},
            "cost_by_doc_type": {},
            "tokens_breakdown": {
                "prompt_tokens": 0,
                "completion_tokens": 0
            }
        } 