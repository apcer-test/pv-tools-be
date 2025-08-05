"""Orchestrator - Public façade for AI document extraction"""

import logging
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

import litellm  # Add this import
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ulid import ULID

from apps.ai_extraction.constants import MIME_PDF
from apps.ai_extraction.exceptions import ExtractionFailedError, PreProcessError
from apps.ai_extraction.models.doctype import DocTypeModel
from apps.ai_extraction.models.fallback import FallbackChainModel, FallbackStepModel
from apps.ai_extraction.models.llm import ExtractionAgentModel, LLMCredentialModel
from apps.ai_extraction.schemas.request import DocType
from apps.ai_extraction.schemas.response import (
    ExtractionDataResult,
    ExtractionError,
    ExtractionResult,
)
from apps.ai_extraction.services.audit_logger import AuditLogger
from apps.ai_extraction.services.fallback_manager import FallbackManager
from apps.ai_extraction.services.preprocessor import PreProcessor
from apps.ai_extraction.services.prompt_registry import PromptRegistry
from core.db import db_session


class Orchestrator:
    """Orchestrator service for AI document extraction"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Initialize with database session and service instances.

        Args:
            session: Database session for service instantiation
        """
        self.session = session
        self.preprocessor = PreProcessor()
        self.prompt_registry = PromptRegistry(session=session)
        self.fallback_manager = FallbackManager(session=session)
        self.audit_logger = AuditLogger(session=session)
        self.logger = logging.getLogger(__name__)

    async def extract_document(
        self,
        request_id: ULID,
        file_path: Path,
        doc_type: DocType,
        audit_logger: Optional[AuditLogger] = None,
        document_intake_id: str = None,
    ) -> Union[ExtractionResult, ExtractionError]:
        """High-level asynchronous API for document extraction.

        This is the main entry point for the AI extraction pipeline. It orchestrates
        the entire process from document preprocessing to final audit logging.

        Args:
            request_id: Externally supplied correlation ULID - ensures idempotency
                    and traces logs end-to-end.
            file_path: Local or mounted path to input document (PDF/TXT).
                    The caller is responsible for staging.
            doc_type: Enum driving prompt & schema selection.
            audit_logger: Optional audit logger instance for logging

        Returns:
            ExtractionResult on success OR ExtractionError on any fatal path.
        """
        # Use provided audit logger or create new one
        logger_instance = audit_logger or self.audit_logger

        try:
            self.logger.info(
                f"Starting document extraction - RequestID: {request_id}, DocType: {doc_type}, File: {file_path}"
            )

            # 1. Pre-processing: Convert document to text
            self.logger.info(
                f"Loading document for preprocessing - RequestID: {request_id}"
            )
            self.preprocessor.load(file_path)

            # 2. Get all active extraction agents for this document type
            self.logger.info(
                f"Loading extraction agents - RequestID: {request_id}, DocType: {doc_type}"
            )

            doc_type_obj = await self.session.scalar(
                select(DocTypeModel)
                .where(DocTypeModel.code == doc_type)
                .options(
                    selectinload(DocTypeModel.extraction_agents)
                    .selectinload(ExtractionAgentModel.fallback_chain)
                    .selectinload(FallbackChainModel.fallback_steps)
                    .selectinload(FallbackStepModel.credential)
                )
            )

            if not doc_type_obj or not doc_type_obj.extraction_agents:
                error_msg = f"No extraction agents configured for doc_type: {doc_type}"
                self.logger.error(
                    f"Agent configuration error - RequestID: {request_id}, Error: {error_msg}"
                )
                raise ExtractionFailedError(error_msg)

            # Filter for active agents and sort by sequence number
            active_agents = sorted(
                [agent for agent in doc_type_obj.extraction_agents if agent.is_active],
                key=lambda a: a.sequence_no,
            )

            if not active_agents:
                error_msg = (
                    f"No active extraction agents found for doc_type: {doc_type}"
                )
                self.logger.error(
                    f"No active agents - RequestID: {request_id}, Error: {error_msg}"
                )
                raise ExtractionFailedError(error_msg)

            self.logger.info(
                f"Found {len(active_agents)} active agents - RequestID: {request_id}"
            )

            # 3. Process each agent to extract different parts of the document
            extraction_results = {}
            total_cost = Decimal("0.00")
            total_latency = 0
            successful_agents = 0

            # Create a mapping of credentials to their uploaded file IDs
            credential_files = {}

            # Get all unique credentials from this agent's fallback chain
            self.logger.info(
                f"Preparing file uploads for LLM providers - RequestID: {request_id}"
            )

            for step in active_agents[0].fallback_chain.fallback_steps:
                credential = await self.fallback_manager._get_credential(
                    step.llm_credential_id
                )
                if not credential:
                    continue

                # Upload file if we haven't already for this credential
                if credential.id not in credential_files:
                    try:
                        uploaded_file = litellm.create_file(
                            file=open(str(file_path), "rb"),
                            purpose="user_data",
                            custom_llm_provider=credential.provider.name.lower(),
                            api_key=credential.api_key,
                        )
                        credential_files[credential.id] = uploaded_file.id
                        self.logger.info(
                            f"File uploaded for credential {credential.id} - RequestID: {request_id}, FileID: {uploaded_file.id}"
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to upload file for credential {credential.id} - RequestID: {request_id}, Error: {str(e)}"
                        )
                        continue

            # Now process each agent with their respective uploaded files
            for agent in active_agents:
                try:
                    self.logger.info(
                        f"Processing agent {agent.code} - RequestID: {request_id}"
                    )

                    # Log agent start
                    await logger_instance.log_agent_start(
                        request_id=request_id,
                        agent_code=agent.code,
                        agent_id=agent.id,
                        template_id=agent.prompt_template_id,
                        doc_type=doc_type,
                    )

                    # Get template from agent and render with document content
                    template_id = agent.prompt_template_id

                    # Get the template content
                    prompt = await self.prompt_registry.render_by_template_id(
                        template_id
                    )
                    self.logger.info(
                        f"Template rendered for agent {agent.code} - RequestID: {request_id}"
                    )

                    # Get the first available uploaded file for this agent's fallback chain
                    uploaded_file_id = None
                    if agent.fallback_chain and agent.fallback_chain.fallback_steps:
                        for step in agent.fallback_chain.fallback_steps:
                            credential = await self.fallback_manager._get_credential(
                                step.llm_credential_id
                            )
                            if credential and credential.id in credential_files:
                                uploaded_file_id = credential_files[credential.id]
                                break

                    if not uploaded_file_id:
                        error_msg = (
                            f"No valid uploaded file found for agent {agent.code}"
                        )
                        self.logger.error(
                            f"File upload error - RequestID: {request_id}, Agent: {agent.code}, Error: {error_msg}"
                        )
                        raise ExtractionFailedError(error_msg)

                    # Create content parts with file reference
                    content_parts = [
                        {"type": "text", "text": prompt},
                        {
                            "type": "file",
                            "file": {"file_id": uploaded_file_id, "format": MIME_PDF},
                        },
                    ]

                    # Execute with agent's fallback chain, passing the content_parts
                    outcome = await self.fallback_manager.execute_with_agent(
                        agent=agent,
                        prompt=content_parts,  # Pass content_parts instead of just prompt
                        doc_type=doc_type,
                        request_id=request_id,
                        audit_logger=logger_instance,
                    )

                    # Process outcome for this agent
                    agent_result = await logger_instance.process_outcome(
                        outcome=outcome,
                        request_id=request_id,
                        template_id=template_id,
                        doc_type=doc_type,
                        agent_code=agent.code,
                    )

                    # Store results by agent code
                    if isinstance(agent_result, ExtractionDataResult):
                        extraction_results.update(agent_result.data["data"])
                        successful_agents += 1

                        # Accumulate costs and latency
                        if agent_result.cost_usd:
                            total_cost += agent_result.cost_usd
                        if agent_result.latency_ms:
                            total_latency += agent_result.latency_ms

                        # Log agent completion
                        await logger_instance.log_agent_complete(
                            request_id=request_id,
                            agent_code=agent.code,
                            agent_id=agent.id,
                            doc_type=doc_type,
                            field_count=(
                                len(agent_result.data) if agent_result.data else 0
                            ),
                            total_cost=agent_result.cost_usd or Decimal("0.00"),
                            total_latency=agent_result.latency_ms or 0,
                            template_id=agent.prompt_template_id,
                        )

                except Exception as e:
                    # Log error for this agent but continue with others
                    error_msg = f"Agent {agent.code} failed: {str(e)}"
                    self.logger.error(
                        f"Agent execution failed - RequestID: {request_id}, Agent: {agent.code}, Error: {error_msg}"
                    )

                    await logger_instance.log_agent_failed(
                        request_id=request_id,
                        agent_code=agent.code,
                        agent_id=agent.id,
                        doc_type=doc_type,
                        error_message=error_msg,
                        template_id=agent.prompt_template_id,
                    )

                    await logger_instance.log_error(
                        request_id=request_id,
                        error_code=f"AGENT_FAILED_{agent.code}",
                        error_message=str(e),
                        failed_at_step=f"agent_{agent.code}",
                    )

            # 4. Combine results from all agents
            if not extraction_results:
                error_msg = "All extraction agents failed"
                self.logger.error(
                    f"All agents failed - RequestID: {request_id}, Error: {error_msg}"
                )
                raise ExtractionFailedError(error_msg)

            # Log extraction completion
            total_fields = len(extraction_results)
            await logger_instance.log_extraction_complete(
                request_id=request_id,
                doc_type=doc_type,
                total_agents=len(active_agents),
                successful_agents=successful_agents,
                total_cost=total_cost,
                total_latency=total_latency,
                total_fields=total_fields,
                template_id=None,
            )

            self.logger.info(
                f"Extraction completed successfully - RequestID: {request_id}, Agents: {successful_agents}/{len(active_agents)}, Fields: {total_fields}, Cost: ${total_cost}, Latency: {total_latency}ms"
            )

            # Return combined results
            return ExtractionResult(
                request_id=request_id, doc_type=doc_type, data=extraction_results
            )

        except PreProcessError as e:
            self.logger.error(
                f"Preprocessing failed - RequestID: {request_id}, Error: {str(e)}"
            )
            return await logger_instance.log_error(
                request_id=request_id,
                error_code="PREPROCESS_FAILED",
                error_message=str(e),
                failed_at_step="preprocessing",
            )
        except ExtractionFailedError as e:
            self.logger.error(
                f"Extraction failed - RequestID: {request_id}, Error: {str(e)}"
            )
            return await logger_instance.log_error(
                request_id=request_id,
                error_code="EXTRACTION_FAILED",
                error_message=str(e),
                failed_at_step="extraction",
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error - RequestID: {request_id}, Error: {str(e)}",
                exc_info=True,
            )
            return await logger_instance.log_error(
                request_id=request_id,
                error_code="UNKNOWN_ERROR",
                error_message=str(e),
                failed_at_step="unknown",
            )
