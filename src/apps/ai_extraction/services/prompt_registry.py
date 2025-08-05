"""Prompt Registry - Template management and rendering"""

from typing import Annotated, Optional, Tuple

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from apps.ai_extraction.exceptions import TemplateNotFoundError, TemplateRenderError
from apps.ai_extraction.models.doctype import DocTypeModel
from apps.ai_extraction.models.prompt_template import PromptTemplateModel
from apps.ai_extraction.schemas.request import DocType, PromptTemplateCreateRequest
from apps.ai_extraction.schemas.response import PromptTemplateResponse
from core.db import db_session


class PromptRegistry:
    """Registry for managing and rendering prompt templates."""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Initialize with database session.

        Args:
            session: Database session for template queries
        """
        self.session = session

    async def render(self, doc_type: DocType) -> Tuple[str, ULID]:
        """Fetch active template from DB, return prompt text.

        Args:
            doc_type: Document type for template selection

        Returns:
            Tuple of (prompt_text, template_id) for audit linkage

        Raises:
            TemplateNotFoundError: When no active template exists for doc_type
        """
        try:
            # Get the active template for this document type
            template_obj = await self._get_active_template(doc_type)

            if not template_obj:
                raise TemplateNotFoundError(
                    f"No active template found for doc_type: {doc_type}"
                )

            # Return the template body directly
            return template_obj.template_body, template_obj.id

        except Exception as e:
            raise TemplateRenderError(f"Unexpected error in prompt retrieval: {str(e)}")

    async def render_by_template_id(self, template_id: ULID) -> str:
        """Render a prompt using a specific template ID.

        Args:
            template_id: ULID of the template to use
            document_text: Document text to include in the prompt

        Returns:
            Rendered prompt text

        Raises:
            TemplateNotFoundError: When template with given ID doesn't exist
            TemplateRenderError: When template rendering fails
        """
        try:
            # Get the template by ID
            template_obj = await self.session.scalar(
                select(PromptTemplateModel).where(PromptTemplateModel.id == template_id)
            )

            if not template_obj:
                raise TemplateNotFoundError(
                    f"Template not found with ID: {template_id}"
                )

            # Replace placeholder with document text if needed
            prompt = template_obj.template_body
            if "{document_text}" in prompt:
                prompt = prompt.replace("{document_text}", document_text)

            return prompt

        except TemplateNotFoundError:
            raise
        except Exception as e:
            raise TemplateRenderError(f"Error rendering template: {str(e)}")

    async def create_template(
        self, template_data: PromptTemplateCreateRequest
    ) -> PromptTemplateResponse:
        """Create a new prompt template.

        Args:
            template_data: The template data to create

        Returns:
            The created template as a response model

        Raises:
            HTTPException: If document type doesn't exist or database error occurs
        """
        try:
            # Check if document type exists
            doc_type = await self.session.get(DocTypeModel, template_data.doc_type_id)
            if not doc_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document type with ID {template_data.doc_type_id} not found",
                )

            # Create new template
            template = PromptTemplateModel(
                doc_type_id=template_data.doc_type_id,
                version=template_data.version,
                language=template_data.language,
                temperature=float(template_data.temperature),
                top_p=float(template_data.top_p),
                max_tokens=template_data.max_tokens,
                template_body=template_data.template_body,
            )

            self.session.add(template)

            # Convert to response model before committing
            response = self._to_response_model(template)

            return response

        except Exception as e:
            # Re-raise HTTPException as is
            if isinstance(e, HTTPException):
                raise
            # Wrap other exceptions
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create prompt template: {str(e)}",
            )

    async def update_template(
        self, template_id: ULID, template_data: PromptTemplateCreateRequest
    ) -> PromptTemplateResponse:
        """Update an existing prompt template.

        Args:
            template_id: The ID of the template to update
            template_data: The updated template data

        Returns:
            The updated template as a response model

        Raises:
            HTTPException: If template or document type doesn't exist
        """
        try:
            # Get the existing template
            template = await self.session.get(PromptTemplateModel, template_id)
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Prompt template with ID {template_id} not found",
                )

            # Check if document type exists if it's being updated
            if template_data.doc_type_id != template.doc_type_id:
                doc_type = await self.session.get(
                    DocTypeModel, template_data.doc_type_id
                )
                if not doc_type:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Document type with ID {template_data.doc_type_id} not found",
                    )

            # Update template fields
            template.doc_type_id = template_data.doc_type_id
            template.version = template_data.version
            template.language = template_data.language
            template.temperature = float(template_data.temperature)
            template.top_p = float(template_data.top_p)
            template.max_tokens = template_data.max_tokens
            template.template_body = template_data.template_body

            return self._to_response_model(template)

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update prompt template: {str(e)}",
            )

    async def get_all_templates(
        self, search: Optional[str] = None
    ) -> list[PromptTemplateResponse]:
        """List all prompt templates with optional filtering.

        Args:
            search: Optional search string to filter by ID

        Returns:
            List of prompt templates matching the filters as response models

        Raises:
            HTTPException: If there's an error executing the query
        """
        try:
            # Build query
            stmt = select(PromptTemplateModel)

            if search:
                stmt = stmt.where(PromptTemplateModel.id == search)

            # Execute query
            result = await self.session.execute(stmt)
            templates = result.scalars().all()

            # Convert to response models
            return [self._to_response_model(template) for template in templates]

        except Exception as e:
            # Log the error and re-raise as HTTPException
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve prompt templates: {str(e)}",
            )

    def _to_response_model(
        self, template: PromptTemplateModel
    ) -> PromptTemplateResponse:
        """Convert a PromptTemplateModel to a PromptTemplateResponse.

        Args:
            template: The template model to convert

        Returns:
            The converted response model
        """
        return PromptTemplateResponse(
            id=template.id,
            doc_type_id=template.doc_type_id,
            version=template.version,
            language=template.language,
            temperature=float(template.temperature),
            top_p=float(template.top_p),
            max_tokens=template.max_tokens,
            template_body=template.template_body,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    async def _get_active_template(
        self, doc_type: DocType
    ) -> PromptTemplateModel | None:
        """Fetch the active template for a document type.

        Args:
            doc_type: Document type to look up

        Returns:
            Active template model or None if not found
        """
        # First get the doc_type record
        doc_type_obj = await self.session.scalar(
            select(DocTypeModel).where(DocTypeModel.code == doc_type)
        )

        if not doc_type_obj:
            return None

        # Get the most recent non-retired template for this doc type
        return await self.session.scalar(
            select(PromptTemplateModel).where(
                PromptTemplateModel.doc_type_id == doc_type_obj.id,
                # PromptTemplateModel.retired_at.is_(None)
            )
        )
