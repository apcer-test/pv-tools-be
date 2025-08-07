"""Fallback Manager - Executes LLM chains with retries and fallbacks"""

import asyncio
import logging
from decimal import Decimal
from typing import Annotated, Any, Dict, Optional

from cryptography.fernet import Fernet
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload
from ulid import ULID

from apps.ai_extraction.exceptions import (
    ChainExhaustedError,
    ProviderError,
    ValidationError,
)
from apps.ai_extraction.models.doctype import DocTypeModel
from apps.ai_extraction.models.fallback import FallbackChainModel, FallbackStepModel
from apps.ai_extraction.models.llm import ExtractionAgentModel, LLMCredentialModel
from apps.ai_extraction.schemas.request import DocType
from apps.ai_extraction.schemas.response import LLMCallResult
from apps.ai_extraction.services.audit_logger import AuditLogger
from apps.ai_extraction.services.llm_gateway import LLMGateway
from apps.ai_extraction.services.schema_validator import SchemaValidator
from core.db import db_session
from config import settings


class FallbackManager:
    """Executes a sequence of models until one produces valid JSON."""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Initialize with database session.

        Args:
            session: Database session for chain queries
        """
        self.session = session
        key = settings.ENCRYPTION_KEY or ""
        self.cipher = Fernet(key.encode())
        self.logger = logging.getLogger(__name__)

    async def execute_with_agent(
        self,
        agent: ExtractionAgentModel,
        prompt: str | list,  # Update type hint to allow list
        doc_type: DocType,
        request_id: ULID,
        audit_logger: Optional[AuditLogger] = None,
    ) -> Dict[str, Any]:
        """Execute fallback chain using a specific extraction agent.

        Args:
            agent: The extraction agent to use
            prompt: Rendered prompt text or list of content parts with file references
            doc_type: Document type for schema validation
            request_id: Request correlation ID
            audit_logger: Optional audit logger for logging

        Returns:
            Dictionary with extraction results and metadata

        Raises:
            ChainExhaustedError: When all models in chain fail
        """
        # Use provided audit logger or create new one
        logger_instance = audit_logger or AuditLogger(self.session)

        if not agent.fallback_chain:
            error_msg = f"No fallback chain configured for agent: {agent.code}"
            self.logger.error(
                f"Fallback chain error - RequestID: {request_id}, Agent: {agent.code}, Error: {error_msg}"
            )
            raise ChainExhaustedError(error_msg)

        # Get steps from chain
        chain = agent.fallback_chain
        steps = chain.fallback_steps

        # If agent has a preferred model, find the step with that model and start from there
        start_index = 0
        if agent.preferred_model:
            preferred_step_index = None
            for i, step in enumerate(steps):
                if step.model.name == agent.preferred_model:
                    preferred_step_index = i
                    break

            if preferred_step_index is not None:
                start_index = preferred_step_index
                self.logger.info(
                    f"Starting from preferred model step {start_index + 1} - RequestID: {request_id}, Agent: {agent.code}, Preferred Model: {agent.preferred_model}"
                )
            else:
                self.logger.warning(
                    f"Preferred model '{agent.preferred_model}' not found in fallback chain - RequestID: {request_id}, Agent: {agent.code}, Starting from first step"
                )

        self.logger.info(
            f"Executing fallback chain - RequestID: {request_id}, Agent: {agent.code}, Steps: {len(steps)}, Start Index: {start_index}"
        )

        last_error = None

        # Try each step in the chain starting from the preferred model step
        for step_index, step in enumerate(steps[start_index:], start=start_index):
            self.logger.info(
                f"Executing step {step_index + 1}/{len(steps)} - RequestID: {request_id}, Agent: {agent.code}, Model: {step.model.name}"
            )

            # Get the credential from the step
            credential = await self._get_credential(step.llm_credential_id)
            if not credential:
                self.logger.warning(
                    f"Credential not found for step {step_index + 1} - RequestID: {request_id}, Agent: {agent.code}, CredentialID: {step.llm_credential_id}"
                )
                continue

            if step.model.is_deprecated:
                self.logger.warning(
                    f"Skipping deprecated model - RequestID: {request_id}, Agent: {agent.code}, Model: {step.model.name}"
                )
                continue

            try:
                # Log LLM call start
                await logger_instance.log_llm_call_start(
                    request_id=request_id,
                    step=step,
                    agent_code=agent.code,
                    model_name=step.model.name,
                    provider=credential.provider.name,
                    doc_type=doc_type,
                    agent_id=agent.id,
                    template_id=agent.prompt_template_id,
                )

                # Make the LLM call
                llm_result = await self._call_llm_with_step(step, prompt, credential)

                # Log successful LLM call
                await logger_instance.log_llm_call_success(
                    request_id=request_id,
                    step=step,
                    agent_code=agent.code,
                    model_name=step.model.name,
                    provider=credential.provider.name,
                    tokens_prompt=llm_result.tokens_prompt,
                    tokens_completion=llm_result.tokens_completion,
                    cost_usd=llm_result.cost_usd,
                    latency_ms=llm_result.latency_ms,
                    doc_type=doc_type,
                    agent_id=agent.id,
                    template_id=agent.prompt_template_id,
                )

                self.logger.info(
                    f"LLM call successful - RequestID: {request_id}, Agent: {agent.code}, Model: {step.model.name}, Tokens: {llm_result.tokens_prompt}/{llm_result.tokens_completion}"
                )

                # Log validation start
                await logger_instance.log_validation_start(
                    request_id=request_id,
                    agent_code=agent.code,
                    doc_type=doc_type,
                    agent_id=agent.id,
                    template_id=agent.prompt_template_id,
                )

                # Validate the response
                validated_data = SchemaValidator.validate(
                    llm_result.response_text, doc_type, agent_code=agent.code
                )

                # Log successful validation
                field_count = (
                    len(validated_data) if isinstance(validated_data, dict) else 0
                )
                await logger_instance.log_validation_success(
                    request_id=request_id,
                    agent_code=agent.code,
                    doc_type=doc_type,
                    field_count=field_count,
                    agent_id=agent.id,
                    template_id=agent.prompt_template_id,
                )

                self.logger.info(
                    f"Validation successful - RequestID: {request_id}, Agent: {agent.code}, Fields: {field_count}"
                )

                # Success! Return with metadata
                return {
                    "data": validated_data,
                    "model_used": step.model.name,
                    "provider": credential.provider.name,
                    "tokens_prompt": llm_result.tokens_prompt,
                    "tokens_completion": llm_result.tokens_completion,
                    "cost_usd": llm_result.cost_usd,
                    "latency_ms": llm_result.latency_ms,
                    "step_index": step_index + 1,
                    "credential_id": credential.id,
                }

            except (ProviderError, ValidationError) as e:
                last_error = e

                # Log the failed attempt
                await logger_instance.log_llm_call_failed(
                    request_id=request_id,
                    step=step,
                    agent_code=agent.code,
                    model_name=step.model.name,
                    provider=credential.provider.name,
                    error_message=str(e),
                    doc_type=doc_type,
                    agent_id=agent.id,
                    template_id=agent.prompt_template_id,
                )

                if isinstance(e, ValidationError):
                    await logger_instance.log_validation_failed(
                        request_id=request_id,
                        agent_code=agent.code,
                        doc_type=doc_type,
                        error_message=str(e),
                        agent_id=agent.id,
                        template_id=agent.prompt_template_id,
                    )

                self.logger.warning(
                    f"Step {step_index + 1} failed - RequestID: {request_id}, Agent: {agent.code}, Model: {step.model.name}, Error: {str(e)}"
                )

                # If this was the preferred model and it failed, log a warning
                if agent.preferred_model and step.model.name == agent.preferred_model:
                    self.logger.warning(
                        f"Preferred model '{agent.preferred_model}' failed validation - RequestID: {request_id}, Agent: {agent.code}"
                    )

                continue

            except Exception as e:
                last_error = e

                await logger_instance.log_llm_call_failed(
                    request_id=request_id,
                    step=step,
                    agent_code=agent.code,
                    model_name=step.model.name,
                    provider=credential.provider.name,
                    error_message=f"Unexpected error: {str(e)}",
                    doc_type=doc_type,
                )

                self.logger.error(
                    f"Unexpected error in step {step_index + 1} - RequestID: {request_id}, Agent: {agent.code}, Model: {step.model.name}, Error: {str(e)}",
                    exc_info=True,
                )
                continue

        # All steps failed
        error_msg = (
            f"Chain exhausted for agent {agent.code}. Last error: {str(last_error)}"
            if last_error
            else f"Chain exhausted for agent {agent.code}"
        )
        self.logger.error(
            f"All steps failed - RequestID: {request_id}, Agent: {agent.code}, Error: {error_msg}"
        )
        raise ChainExhaustedError(error_msg)

    async def execute(
        self,
        prompt: str,
        doc_type: DocType,
        request_id: ULID,
        audit_logger: Optional[AuditLogger] = None,
    ) -> Dict[str, Any]:
        """Execute fallback chain until valid output is produced.

        Args:
            prompt: Rendered prompt to send to LLMs
            doc_type: Document type for schema validation
            request_id: Request correlation ID
            audit_logger: Optional audit logger for logging

        Returns:
            Dictionary with extraction results and metadata

        Raises:
            ChainExhaustedError: When all models in chain fail
        """
        # Load the extraction agent and fallback chain for this document type
        agent = await self._load_agent_for_doc_type(doc_type)

        if not agent or not agent.fallback_chain:
            error_msg = f"No extraction agent or fallback chain configured for doc_type: {doc_type}"
            self.logger.error(
                f"Agent configuration error - RequestID: {request_id}, Error: {error_msg}"
            )
            raise ChainExhaustedError(error_msg)

        # Use the execute_with_agent method
        return await self.execute_with_agent(
            agent=agent,
            prompt=prompt,
            doc_type=doc_type,
            request_id=request_id,
            audit_logger=audit_logger,
        )

    async def _load_agent_for_doc_type(
        self, doc_type: DocType
    ) -> ExtractionAgentModel | None:
        """Load the active extraction agent for a document type.

        Args:
            doc_type: Document type to look up

        Returns:
            ExtractionAgentModel or None if not found
        """
        # Get extraction agent for this document type
        doc_type_obj = await self.session.scalar(
            select(DocTypeModel)
            .where(DocTypeModel.code == doc_type)
            .options(
                selectinload(DocTypeModel.extraction_agents)
                .selectinload(ExtractionAgentModel.fallback_chain)
                .selectinload(FallbackChainModel.fallback_steps)
                .selectinload(FallbackStepModel.model)
            )
        )
        agent = None
        if doc_type_obj and doc_type_obj.extraction_agents:
            # Pick the first active agent with the lowest sequence_no
            active_agents = [a for a in doc_type_obj.extraction_agents if a.is_active]
            if active_agents:
                agent = sorted(active_agents, key=lambda a: a.sequence_no)[0]

        return agent

    async def _get_credential(self, credential_id: ULID) -> LLMCredentialModel | None:
        """Get a credential by ID and decrypt its API key.

        Args:
            credential_id: Credential ULID

        Returns:
            Credential with decrypted API key or None
        """
        credential = await self.session.scalar(
            select(LLMCredentialModel)
            .where(
                LLMCredentialModel.id == credential_id,
                LLMCredentialModel.is_active == True,
            )
            .options(
                selectinload(LLMCredentialModel.provider),
                selectinload(LLMCredentialModel.fallback_steps).selectinload(
                    FallbackStepModel.model
                ),
            )
        )

        if not credential:
            return None

        try:
            # Decrypt the API key
            decrypted_key = self.cipher.decrypt(credential.api_key_enc).decode("utf-8")
            credential.api_key = decrypted_key
            return credential
        except Exception as e:
            self.logger.error(f"Failed to decrypt credential {credential_id}: {str(e)}")
            return None

    async def _call_llm_with_step(
        self,
        step: FallbackStepModel,
        prompt: str | list,  # Update type hint to allow list
        credential: LLMCredentialModel,
    ) -> LLMCallResult:
        """Call LLM using step configuration.

        Args:
            step: Fallback step with model and overrides
            prompt: Prompt text or list of content parts with file references
            credential: Credential to use

        Returns:
            LLM call result
        """
        return await LLMGateway.call(
            provider=credential.provider.name,
            model=step.model.name,
            prompt=prompt,
            max_tokens=step.max_tokens_override or 1024,
            temperature=float(step.temperature_override or 0.0),
            credential=credential,
            timeout=30,
        )

    async def _log_step_attempt(
        self,
        step: FallbackStepModel,
        request_id: ULID,
        error: str | None = None,
        llm_result: LLMCallResult | None = None,
        status: str = "FAILED",
        agent_code: str | None = None,
    ) -> None:
        """Log a step attempt to audit trail.

        Args:
            step: The step that was attempted
            request_id: Request correlation ID
            error: Error message if failed
            llm_result: LLM result if successful
            status: Step status
            agent_code: Code of the extraction agent
        """
        # This method is now handled by the audit logger integration
        pass
