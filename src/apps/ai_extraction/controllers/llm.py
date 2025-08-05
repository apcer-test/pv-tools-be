from typing import Annotated, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from ulid import ULID

from apps.ai_extraction.schemas.request import (
    LLMCredentialCreateRequest,
    LLMModelCreateRequest,
    LLMProviderCreateRequest,
)
from apps.ai_extraction.schemas.response import (
    LLMCredentialDetailResponse,
    LLMCredentialResponse,
    LLMModelDetailResponse,
    LLMModelResponse,
    LLMProviderDetailResponse,
    LLMProviderResponse,
)
from apps.ai_extraction.services.llm import LLMService
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/api/llm", tags=["LLM Management"])


# LLM Provider Endpoints
@router.post(
    "/providers",
    status_code=status.HTTP_201_CREATED,
    name="Create LLM Provider",
    description="Create a new LLM provider",
    operation_id="create_llm_provider",
    response_model=BaseResponse[LLMProviderResponse],
    responses={
        201: {"description": "LLM provider created successfully"},
        400: {"description": "Provider with same name already exists"},
        500: {"description": "Internal server error"},
    },
)
async def create_provider(
    request: Annotated[LLMProviderCreateRequest, Body()],
    service: Annotated[LLMService, Depends()],
) -> BaseResponse[LLMProviderResponse]:
    """
    Create a new LLM provider.

    This endpoint creates a new LLM provider with the specified details.
    The provider name must be unique.

    Args:
        request: Provider creation request containing name, base_url, and is_active
        service: LLMService instance for business logic

    Returns:
        BaseResponse[LLMProviderResponse]: Created provider details

    Raises:
        HTTPException: If provider with same name already exists
    """
    try:
        provider = await service.create_provider(request)
        return BaseResponse(data=provider)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the provider: {str(e)}",
        )


@router.get(
    "/providers",
    status_code=status.HTTP_200_OK,
    name="Get All LLM Providers",
    description="Get all LLM providers with optional filtering",
    operation_id="get_all_llm_providers",
    response_model=BaseResponse[List[LLMProviderResponse]],
    responses={
        200: {"description": "List of LLM providers"},
        500: {"description": "Internal server error"},
    },
)
async def get_all_providers(
    service: Annotated[LLMService, Depends()],
    search: Optional[str] = Query(None, description="Search by provider name"),
    include_inactive: bool = Query(False, description="Include inactive providers"),
) -> BaseResponse[List[LLMProviderResponse]]:
    """
    Get all LLM providers.

    This endpoint returns a list of all LLM providers with optional filtering.

    Args:
        service: LLMService instance for business logic
        search: Optional search term to filter by provider name
        include_inactive: Whether to include inactive providers

    Returns:
        BaseResponse[List[LLMProviderResponse]]: List of providers
    """
    try:
        providers = await service.get_all_providers(
            search=search, include_inactive=include_inactive
        )
        return BaseResponse(data=providers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching providers: {str(e)}",
        )


@router.get(
    "/providers/{provider_id}",
    status_code=status.HTTP_200_OK,
    name="Get LLM Provider by ID",
    description="Get a specific LLM provider by ID with related data",
    operation_id="get_llm_provider_by_id",
    response_model=BaseResponse[LLMProviderDetailResponse],
    responses={
        200: {"description": "LLM provider details with related data"},
        404: {"description": "Provider not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_provider_by_id(
    provider_id: Annotated[ULID, Path(description="Provider ULID")],
    service: Annotated[LLMService, Depends()],
) -> BaseResponse[LLMProviderDetailResponse]:
    """
    Get a specific LLM provider by ID.

    This endpoint returns detailed information about a specific LLM provider
    including its models and credentials.

    Args:
        provider_id: Provider ULID
        service: LLMService instance for business logic

    Returns:
        BaseResponse[LLMProviderDetailResponse]: Provider details with related data

    Raises:
        HTTPException: If provider not found
    """
    try:
        provider = await service.get_provider_by_id(provider_id)
        return BaseResponse(data=provider)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the provider: {str(e)}",
        )


# LLM Model Endpoints
@router.post(
    "/models",
    status_code=status.HTTP_201_CREATED,
    name="Create LLM Model",
    description="Create a new LLM model",
    operation_id="create_llm_model",
    response_model=BaseResponse[LLMModelResponse],
    responses={
        201: {"description": "LLM model created successfully"},
        400: {"description": "Provider not found or model name conflict"},
        500: {"description": "Internal server error"},
    },
)
async def create_model(
    request: Annotated[LLMModelCreateRequest, Body()],
    service: Annotated[LLMService, Depends()],
) -> BaseResponse[LLMModelResponse]:
    """
    Create a new LLM model.

    This endpoint creates a new LLM model for a specific provider.
    The model name must be unique within the provider.

    Args:
        request: Model creation request containing provider_id, name, pricing, etc.
        service: LLMService instance for business logic

    Returns:
        BaseResponse[LLMModelResponse]: Created model details

    Raises:
        HTTPException: If provider not found or model name conflict
    """
    try:
        model = await service.create_model(request)
        return BaseResponse(data=model)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the model: {str(e)}",
        )


@router.get(
    "/models",
    status_code=status.HTTP_200_OK,
    name="Get All LLM Models",
    description="Get all LLM models with optional filtering",
    operation_id="get_all_llm_models",
    response_model=BaseResponse[List[LLMModelDetailResponse]],
    responses={
        200: {"description": "List of LLM models"},
        500: {"description": "Internal server error"},
    },
)
async def get_all_models(
    service: Annotated[LLMService, Depends()],
    provider_id: Optional[ULID] = Query(None, description="Filter by provider ID"),
    search: Optional[str] = Query(None, description="Search by model name"),
    include_deprecated: bool = Query(False, description="Include deprecated models"),
) -> BaseResponse[List[LLMModelDetailResponse]]:
    """
    Get all LLM models.

    This endpoint returns a list of all LLM models with optional filtering.

    Args:
        service: LLMService instance for business logic
        provider_id: Optional provider ID to filter by
        search: Optional search term to filter by model name
        include_deprecated: Whether to include deprecated models

    Returns:
        BaseResponse[List[LLMModelDetailResponse]]: List of models with provider details
    """
    try:
        models = await service.get_all_models(
            provider_id=provider_id,
            search=search,
            include_deprecated=include_deprecated,
        )
        return BaseResponse(data=models)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching models: {str(e)}",
        )


@router.get(
    "/models/{model_id}",
    status_code=status.HTTP_200_OK,
    name="Get LLM Model by ID",
    description="Get a specific LLM model by ID with provider details",
    operation_id="get_llm_model_by_id",
    response_model=BaseResponse[LLMModelDetailResponse],
    responses={
        200: {"description": "LLM model details with provider info"},
        404: {"description": "Model not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_model_by_id(
    model_id: Annotated[ULID, Path(description="Model ULID")],
    service: Annotated[LLMService, Depends()],
) -> BaseResponse[LLMModelDetailResponse]:
    """
    Get a specific LLM model by ID.

    This endpoint returns detailed information about a specific LLM model
    including its provider details.

    Args:
        model_id: Model ULID
        service: LLMService instance for business logic

    Returns:
        BaseResponse[LLMModelDetailResponse]: Model details with provider info

    Raises:
        HTTPException: If model not found
    """
    try:
        model = await service.get_model_by_id(model_id)
        return BaseResponse(data=model)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the model: {str(e)}",
        )


# LLM Credential Endpoints
@router.post(
    "/credentials",
    status_code=status.HTTP_201_CREATED,
    name="Create LLM Credential",
    description="Create a new LLM credential with encrypted API key",
    operation_id="create_llm_credential",
    response_model=BaseResponse[LLMCredentialResponse],
    responses={
        201: {"description": "LLM credential created successfully"},
        400: {"description": "Provider not found or alias conflict"},
        500: {"description": "Internal server error"},
    },
)
async def create_credential(
    request: Annotated[LLMCredentialCreateRequest, Body()],
    service: Annotated[LLMService, Depends()],
) -> BaseResponse[LLMCredentialResponse]:
    """
    Create a new LLM credential.

    This endpoint creates a new LLM credential for a specific provider.
    The API key will be encrypted before storage. The alias must be unique
    within the provider if provided.

    Args:
        request: Credential creation request containing provider_id, api_key, etc.
        service: LLMService instance for business logic

    Returns:
        BaseResponse[LLMCredentialResponse]: Created credential details (without API key)

    Raises:
        HTTPException: If provider not found or alias conflict
    """
    try:
        credential = await service.create_credential(request)
        return BaseResponse(data=credential)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the credential: {str(e)}",
        )


@router.get(
    "/credentials",
    status_code=status.HTTP_200_OK,
    name="Get All LLM Credentials",
    description="Get all LLM credentials with optional filtering",
    operation_id="get_all_llm_credentials",
    response_model=BaseResponse[List[LLMCredentialDetailResponse]],
    responses={
        200: {"description": "List of LLM credentials"},
        500: {"description": "Internal server error"},
    },
)
async def get_all_credentials(
    service: Annotated[LLMService, Depends()],
    provider_id: Optional[ULID] = Query(None, description="Filter by provider ID"),
    search: Optional[str] = Query(None, description="Search by credential alias"),
    include_inactive: bool = Query(False, description="Include inactive credentials"),
) -> BaseResponse[List[LLMCredentialDetailResponse]]:
    """
    Get all LLM credentials.

    This endpoint returns a list of all LLM credentials with optional filtering.
    API keys are not included in the response for security reasons.

    Args:
        service: LLMService instance for business logic
        provider_id: Optional provider ID to filter by
        search: Optional search term to filter by credential alias
        include_inactive: Whether to include inactive credentials

    Returns:
        BaseResponse[List[LLMCredentialDetailResponse]]: List of credentials with provider details
    """
    try:
        credentials = await service.get_all_credentials(
            provider_id=provider_id, search=search, include_inactive=include_inactive
        )
        return BaseResponse(data=credentials)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching credentials: {str(e)}",
        )


@router.get(
    "/credentials/{credential_id}",
    status_code=status.HTTP_200_OK,
    name="Get LLM Credential by ID",
    description="Get a specific LLM credential by ID with provider details",
    operation_id="get_llm_credential_by_id",
    response_model=BaseResponse[LLMCredentialDetailResponse],
    responses={
        200: {"description": "LLM credential details with provider info"},
        404: {"description": "Credential not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_credential_by_id(
    credential_id: Annotated[ULID, Path(description="Credential ULID")],
    service: Annotated[LLMService, Depends()],
) -> BaseResponse[LLMCredentialDetailResponse]:
    """
    Get a specific LLM credential by ID.

    This endpoint returns detailed information about a specific LLM credential
    including its provider details. API key is not included for security reasons.

    Args:
        credential_id: Credential ULID
        service: LLMService instance for business logic

    Returns:
        BaseResponse[LLMCredentialDetailResponse]: Credential details with provider info

    Raises:
        HTTPException: If credential not found
    """
    try:
        credential = await service.get_credential_by_id(credential_id)
        return BaseResponse(data=credential)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the credential: {str(e)}",
        )
