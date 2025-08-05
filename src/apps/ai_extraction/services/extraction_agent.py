"""Extraction Agent Service - Manages AI extraction agents"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from apps.ai_extraction.models.doctype import DocTypeModel
from apps.ai_extraction.models.fallback import FallbackChainModel
from apps.ai_extraction.models.llm import (
    ExtractionAgentModel,
    LLMCredentialModel,
    LLMModel,
)
from apps.ai_extraction.models.prompt_template import PromptTemplateModel
from apps.ai_extraction.schemas.request import ExtractionAgentCreateRequest
from core.db import db_session
from core.utils.schema import SuccessResponse


class ExtractionAgentService:
    """Service for managing extraction agents"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Initialize with database session.

        Args:
            session: Database session for agent operations
        """
        self.session = session

    async def validate_references(
        self, doc_type_id: ULID, template_id: ULID, chain_id: ULID, credential_id: ULID
    ) -> None:
        """Validate that all referenced IDs exist in the database.

        Args:
            doc_type_id: Document type ID to validate
            template_id: Template ID to validate
            chain_id: Chain ID to validate
            credential_id: Credential ID to validate

        Raises:
            HTTPException: If any of the referenced IDs don't exist
        """
        # Check doc_type_id exists
        doc_type = await self.session.scalar(
            select(DocTypeModel).where(DocTypeModel.id == doc_type_id)
        )
        if not doc_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document type with ID {doc_type_id} not found",
            )

        # Check template_id exists
        template = await self.session.scalar(
            select(PromptTemplateModel).where(PromptTemplateModel.id == template_id)
        )
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template with ID {template_id} not found",
            )

        # Check chain_id exists
        chain = await self.session.scalar(
            select(FallbackChainModel).where(FallbackChainModel.id == chain_id)
        )
        if not chain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fallback chain with ID {chain_id} not found",
            )

        # Check credential_id exists
        credential = await self.session.scalar(
            select(LLMCredentialModel).where(LLMCredentialModel.id == credential_id)
        )
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM credential with ID {credential_id} not found",
            )

    async def create_agent(
        self, request: ExtractionAgentCreateRequest
    ) -> SuccessResponse:
        """Create a new extraction agent.

        Args:
            data: Agent creation request data

        Returns:
            Created agent response
        """
        # Validate that all referenced IDs exist
        await self.validate_references(
            str(request.doc_type_id),
            str(request.template_id),
            str(request.chain_id),
            str(request.credential_id),
        )

        # Create agent model
        agent = ExtractionAgentModel(
            doc_type_id=str(request.doc_type_id),
            prompt_template_id=str(request.template_id),
            fallback_chain_id=str(request.chain_id),
            llm_credential_id=str(request.credential_id),
            code=request.code,
            description=request.description,
            is_active=request.is_active,
            sequence_no=request.seq_no,
            name=f"Agent {request.seq_no}",
        )

        self.session.add(agent)

        return SuccessResponse(message="Extraction agent created successfully")

    async def update_agent(
        self,
        agent_id: ULID,
        doc_type_id: ULID,
        template_id: ULID,
        chain_id: ULID,
        credential_id: ULID,
        code: str,
        description: str,
        is_active: bool,
        seq_no: int,
    ) -> SuccessResponse:
        """Update an existing extraction agent.

        Args:
            agent_id: ID of the agent to update
            data: Agent update request data

        Returns:
            Updated agent response
        """
        # Check if agent exists
        agent = await self.session.scalar(
            select(ExtractionAgentModel).where(ExtractionAgentModel.id == agent_id)
        )
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction agent with ID {agent_id} not found",
            )

        # Validate that all referenced IDs exist
        await self.validate_references(
            doc_type_id, template_id, chain_id, credential_id
        )

        update_data = {
            "doc_type_id": doc_type_id,
            "prompt_template_id": template_id,
            "fallback_chain_id": chain_id,
            "llm_credential_id": credential_id,
            "code": code,
            "description": description,
            "is_active": is_active,
            "sequence_no": seq_no,
        }

        await self.session.execute(
            update(ExtractionAgentModel)
            .where(ExtractionAgentModel.id == agent_id)
            .values(**update_data)
        )

        return SuccessResponse(message="Extraction agent updated successfully")
