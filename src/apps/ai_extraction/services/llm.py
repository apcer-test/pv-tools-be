from sqlalchemy import select, and_, or_
from typing import Annotated, List, Optional
from ulid import ULID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import date

from apps.ai_extraction.models.llm import (
    LLMProviderModel, 
    LLMModel, 
    LLMCredentialModel
)
from apps.ai_extraction.schemas.request import (
    LLMProviderCreateRequest,
    LLMModelCreateRequest,
    LLMCredentialCreateRequest
)
from apps.ai_extraction.schemas.response import (
    LLMProviderResponse,
    LLMProviderDetailResponse,
    LLMModelResponse,
    LLMModelDetailResponse,
    LLMCredentialResponse,
    LLMCredentialDetailResponse
)
from core.db import db_session
from core.common_helpers import encryption


class LLMService:
    """Service class for handling LLM operations"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]):
        """Initialize the LLMService with a database session"""
        self.session = session

    # LLM Provider Methods
    async def create_provider(self, request: LLMProviderCreateRequest) -> LLMProviderResponse:
        """
        Create a new LLM provider.
        
        Args:
            request: Provider creation request
            
        Returns:
            LLMProviderResponse: Created provider details
            
        Raises:
            HTTPException: If provider with same name already exists
        """
        # Check if provider with same name already exists
        existing_provider = await self.session.scalar(
            select(LLMProviderModel).where(LLMProviderModel.name == request.name)
        )
        
        if existing_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider with name '{request.name}' already exists"
            )
        
        # Create new provider
        provider = LLMProviderModel(
            name=request.name,
            base_url=request.base_url,
            is_active=request.is_active
        )
        
        self.session.add(provider)
        
        return LLMProviderResponse(
            id=provider.id,
            name=provider.name,
            base_url=provider.base_url,
            is_active=provider.is_active,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )

    async def get_all_providers(
        self, 
        search: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[LLMProviderResponse]:
        """
        Get all LLM providers.
        
        Args:
            search: Optional search term to filter by provider name
            include_inactive: Whether to include inactive providers
            
        Returns:
            List[LLMProviderResponse]: List of providers
        """
        stmt = select(LLMProviderModel)
        
        # Apply filters
        if not include_inactive:
            stmt = stmt.where(LLMProviderModel.is_active == True)
        
        if search:
            stmt = stmt.where(LLMProviderModel.name.ilike(f"%{search}%"))
        
        result = await self.session.execute(stmt)
        providers = result.scalars().all()
        
        return [
            LLMProviderResponse(
                id=provider.id,
                name=provider.name,
                base_url=provider.base_url,
                is_active=provider.is_active,
                created_at=provider.created_at,
                updated_at=provider.updated_at
            )
            for provider in providers
        ]

    async def get_provider_by_id(self, provider_id: ULID) -> LLMProviderDetailResponse:
        """
        Get a provider by ID with related data.
        
        Args:
            provider_id: Provider ULID
            
        Returns:
            LLMProviderDetailResponse: Provider details with related data
            
        Raises:
            HTTPException: If provider not found
        """
        provider = await self.session.scalar(
            select(LLMProviderModel)
            .where(LLMProviderModel.id == str(provider_id))
            .options(
                selectinload(LLMProviderModel.models),
                selectinload(LLMProviderModel.credentials)
            )
        )
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Convert models to response format
        models = [
            LLMModelResponse(
                id=model.id,
                provider_id=model.provider_id,
                name=model.name,
                context_tokens=model.context_tokens,
                input_price_1k=model.input_price_1k,
                output_price_1k=model.output_price_1k,
                launch_date=model.launch_date,
                is_deprecated=model.is_deprecated,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
            for model in provider.models
        ]
        
        # Convert credentials to response format
        credentials = [
            LLMCredentialResponse(
                id=cred.id,
                provider_id=cred.provider_id,
                alias=cred.alias,
                rate_limit_rpm=cred.rate_limit_rpm,
                is_active=cred.is_active,
                created_at=cred.created_at,
                updated_at=cred.updated_at
            )
            for cred in provider.credentials
        ]
        
        return LLMProviderDetailResponse(
            id=provider.id,
            name=provider.name,
            base_url=provider.base_url,
            is_active=provider.is_active,
            models=models,
            credentials=credentials,
            created_at=provider.created_at,
            updated_at=provider.updated_at
        )

    # LLM Model Methods
    async def create_model(self, request: LLMModelCreateRequest) -> LLMModelResponse:
        """
        Create a new LLM model.
        
        Args:
            request: Model creation request
            
        Returns:
            LLMModelResponse: Created model details
            
        Raises:
            HTTPException: If provider not found or model name conflict
        """
        # Verify provider exists
        provider = await self.session.scalar(
            select(LLMProviderModel).where(LLMProviderModel.id == str(request.provider_id))
        )
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Check if model with same name already exists for this provider
        existing_model = await self.session.scalar(
            select(LLMModel)
            .where(
                and_(
                    LLMModel.provider_id == str(request.provider_id),
                    LLMModel.name == request.name
                )
            )
        )
        
        if existing_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model with name '{request.name}' already exists for this provider"
            )
        
        # Create new model
        model = LLMModel(
            provider_id=str(request.provider_id),
            name=request.name,
            context_tokens=request.context_tokens,
            input_price_1k=request.input_price_1k,
            output_price_1k=request.output_price_1k,
            launch_date=request.launch_date,
            is_deprecated=request.is_deprecated
        )
        
        self.session.add(model)
        
        return LLMModelResponse(
            id=model.id,
            provider_id=model.provider_id,
            name=model.name,
            context_tokens=model.context_tokens,
            input_price_1k=model.input_price_1k,
            output_price_1k=model.output_price_1k,
            launch_date=model.launch_date,
            is_deprecated=model.is_deprecated,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_all_models(
        self,
        provider_id: Optional[ULID] = None,
        search: Optional[str] = None,
        include_deprecated: bool = False
    ) -> List[LLMModelDetailResponse]:
        """
        Get all LLM models.
        
        Args:
            provider_id: Optional provider ID to filter by
            search: Optional search term to filter by model name
            include_deprecated: Whether to include deprecated models
            
        Returns:
            List[LLMModelDetailResponse]: List of models with provider details
        """
        stmt = (
            select(LLMModel)
            .options(selectinload(LLMModel.provider))
        )
        
        # Apply filters
        if provider_id:
            stmt = stmt.where(LLMModel.provider_id == str(provider_id))
        
        if not include_deprecated:
            stmt = stmt.where(LLMModel.is_deprecated == False)
        
        if search:
            stmt = stmt.where(LLMModel.name.ilike(f"%{search}%"))
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [
            LLMModelDetailResponse(
                id=model.id,
                provider_id=model.provider_id,
                provider_name=model.provider.name,
                name=model.name,
                context_tokens=model.context_tokens,
                input_price_1k=model.input_price_1k,
                output_price_1k=model.output_price_1k,
                launch_date=model.launch_date,
                is_deprecated=model.is_deprecated,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
            for model in models
        ]

    async def get_model_by_id(self, model_id: ULID) -> LLMModelDetailResponse:
        """
        Get a model by ID with provider details.
        
        Args:
            model_id: Model ULID
            
        Returns:
            LLMModelDetailResponse: Model details with provider info
            
        Raises:
            HTTPException: If model not found
        """
        model = await self.session.scalar(
            select(LLMModel)
            .where(LLMModel.id == str(model_id))
            .options(selectinload(LLMModel.provider))
        )
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        return LLMModelDetailResponse(
            id=model.id,
            provider_id=model.provider_id,
            provider_name=model.provider.name,
            name=model.name,
            context_tokens=model.context_tokens,
            input_price_1k=model.input_price_1k,
            output_price_1k=model.output_price_1k,
            launch_date=model.launch_date,
            is_deprecated=model.is_deprecated,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    # LLM Credential Methods
    async def create_credential(self, request: LLMCredentialCreateRequest) -> LLMCredentialResponse:
        """
        Create a new LLM credential.
        
        Args:
            request: Credential creation request
            
        Returns:
            LLMCredentialResponse: Created credential details
            
        Raises:
            HTTPException: If provider not found or alias conflict
        """
        # Verify provider exists
        provider = await self.session.scalar(
            select(LLMProviderModel).where(LLMProviderModel.id == str(request.provider_id))
        )
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Check for alias conflict if alias is provided
        if request.alias:
            existing_credential = await self.session.scalar(
                select(LLMCredentialModel)
                .where(
                    and_(
                        LLMCredentialModel.provider_id == str(request.provider_id),
                        LLMCredentialModel.alias == request.alias
                    )
                )
            )
            
            if existing_credential:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Credential with alias '{request.alias}' already exists for this provider"
                )
        
        # Encrypt the API key
        encrypted_api_key = await encryption(request.api_key)
        
        # Create new credential
        credential = LLMCredentialModel(
            provider_id=str(request.provider_id),
            alias=request.alias,
            api_key_enc=encrypted_api_key,
            rate_limit_rpm=request.rate_limit_rpm,
            is_active=request.is_active
        )
        
        self.session.add(credential)
        
        return LLMCredentialResponse(
            id=credential.id,
            provider_id=credential.provider_id,
            alias=credential.alias,
            rate_limit_rpm=credential.rate_limit_rpm,
            is_active=credential.is_active,
            created_at=credential.created_at,
            updated_at=credential.updated_at
        )

    async def get_all_credentials(
        self,
        provider_id: Optional[ULID] = None,
        search: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[LLMCredentialDetailResponse]:
        """
        Get all LLM credentials.
        
        Args:
            provider_id: Optional provider ID to filter by
            search: Optional search term to filter by alias
            include_inactive: Whether to include inactive credentials
            
        Returns:
            List[LLMCredentialDetailResponse]: List of credentials with provider details
        """
        stmt = (
            select(LLMCredentialModel)
            .options(selectinload(LLMCredentialModel.provider))
        )
        
        # Apply filters
        if provider_id:
            stmt = stmt.where(LLMCredentialModel.provider_id == str(provider_id))
        
        if not include_inactive:
            stmt = stmt.where(LLMCredentialModel.is_active == True)
        
        if search:
            stmt = stmt.where(LLMCredentialModel.alias.ilike(f"%{search}%"))
        
        result = await self.session.execute(stmt)
        credentials = result.scalars().all()
        
        return [
            LLMCredentialDetailResponse(
                id=cred.id,
                provider_id=cred.provider_id,
                provider_name=cred.provider.name,
                alias=cred.alias,
                rate_limit_rpm=cred.rate_limit_rpm,
                is_active=cred.is_active,
                created_at=cred.created_at,
                updated_at=cred.updated_at
            )
            for cred in credentials
        ]

    async def get_credential_by_id(self, credential_id: ULID) -> LLMCredentialDetailResponse:
        """
        Get a credential by ID with provider details.
        
        Args:
            credential_id: Credential ULID
            
        Returns:
            LLMCredentialDetailResponse: Credential details with provider info
            
        Raises:
            HTTPException: If credential not found
        """
        credential = await self.session.scalar(
            select(LLMCredentialModel)
            .where(LLMCredentialModel.id == str(credential_id))
            .options(selectinload(LLMCredentialModel.provider))
        )
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        return LLMCredentialDetailResponse(
            id=credential.id,
            provider_id=credential.provider_id,
            provider_name=credential.provider.name,
            alias=credential.alias,
            rate_limit_rpm=credential.rate_limit_rpm,
            is_active=credential.is_active,
            created_at=credential.created_at,
            updated_at=credential.updated_at
        )
