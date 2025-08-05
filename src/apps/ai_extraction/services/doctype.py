from sqlalchemy import select
from typing import Annotated, List, Optional
from ulid import ULID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.ai_extraction.models.doctype import DocTypeModel
from apps.ai_extraction.schemas.response import DocumentTypeResponse, PromptTemplateResponse, ExtractionAgentResponse
from core.db import db_session


class DocTypeService:
    """Service class for handling document type operations"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]):
        """Initialize the DocTypeService with a database session"""
        self.session = session

    async def get_all_doc_types(
        self,
        search: Optional[str] = None
    ) -> List[DocumentTypeResponse]:
        """
        Get all document types with their related data.
        
        Args:
            search: Optional search term to filter by document type ID or code
                   (case-insensitive partial match for code, exact match for ULID)
            
        Returns:
            List[DocumentTypeResponse]: List of matching document types with related data
            
        Raises:
            HTTPException: If no document types are found
        """
        # Build the base query
        stmt = (
            select(DocTypeModel)
            .options(
                selectinload(DocTypeModel.prompt_templates),
                selectinload(DocTypeModel.extraction_agents)
            )
        )
        
        # Apply search filter if provided
        if search:
            try:
                search_ulid = ULID.from_str(search)
                stmt = stmt.where(DocTypeModel.id == str(search_ulid))
            except ValueError:
                # If not a valid ULID, search by code (case-insensitive partial match)
                stmt = stmt.where(DocTypeModel.code.ilike(f"%{search}%"))
        
        result = await self.session.execute(stmt)
        doc_types = result.scalars().all()
        
        if not doc_types:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No document types found"
            )
        
        # Create document type response
        response = []
        for doc_type in doc_types:
            # Create prompt templates response
            prompt_templates = [
                PromptTemplateResponse(
                    id=template.id,
                    doc_type_id=doc_type.id,
                    version=template.version,
                    language=template.language,
                    temperature=float(template.temperature),
                    top_p=float(template.top_p),
                    max_tokens=template.max_tokens,
                    created_at=template.created_at,
                    template_body=template.template_body
                )
                for template in doc_type.prompt_templates
            ]
            
            # Create extraction agents response
            extraction_agents = [
                ExtractionAgentResponse(
                    id=agent.id,
                    code=agent.code,
                    name=agent.name,
                    description=agent.description,
                    sequence_no=agent.sequence_no,
                    is_active=agent.is_active
                )
                for agent in doc_type.extraction_agents
            ]
            
            # Create document type response
            doc_type_response = DocumentTypeResponse(
                id=doc_type.id,
                code=doc_type.code,
                description=doc_type.description,
                prompt_templates=prompt_templates,
                extraction_agents=extraction_agents
            )
            response.append(doc_type_response)
            
        return response