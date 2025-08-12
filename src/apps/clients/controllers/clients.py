from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status
from fastapi_pagination import Page

from core.auth import AdminHasPermission
from core.utils.schema import BaseResponse
from apps.clients.schemas.request import CreateClientRequest, UpdateClientRequest, ListClientsRequest
from apps.clients.schemas.response import ClientResponse, ClientListResponse, CreateClientResponse, UpdateClientResponse, DeleteClientResponse
from apps.clients.services.clients import ClientService
from apps.users.models.user import Users

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponse[CreateClientResponse],
    #dependencies=[Depends(AdminHasPermission())],
    name="Create Client",
    description="Create a new client (Admin only)"
)
async def create_client(
    client_data: CreateClientRequest,
    service: Annotated[ClientService, Depends()],
    #user: Annotated[Users, Depends(AdminHasPermission())]
) -> BaseResponse[CreateClientResponse]:
    """
    Create a new client.
    
    This endpoint requires admin permissions and creates a new client with the provided data.
    If media information is provided, it will also create the associated media record.
    
    Args:
        client_data: Client creation data including name, code, slug, and optional media
        service: ClientService instance for business logic
        user: Authenticated admin user
        
    Returns:
        BaseResponse with created client ID and success message
        
    Raises:
        ConflictError: If client with same name, code, or slug already exists
    """
    client = await service.create_client(client_data, '01K24Y1B8SYB3GGQDFM56333M2')
    
    return BaseResponse(
        data=CreateClientResponse(
            id=str(client.id),
            message="Client created successfully"
        )
    )


@router.get(
    "/{client_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[ClientResponse],
    name="Get Client",
    description="Get client by ID"
)
async def get_client(
    service: Annotated[ClientService, Depends()],
    client_id: str = Path(..., description="Client ID"),
) -> BaseResponse[ClientResponse]:
    """
    Get client details by ID.
    
    Args:
        client_id: ID of the client to retrieve
        service: ClientService instance for business logic
        
    Returns:
        BaseResponse with client details
        
    Raises:
        NotFoundError: If client not found
    """
    client = await service.get_client_by_id(client_id)
    
    return BaseResponse(data=service._to_response(client))


@router.put(
    "/{client_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[UpdateClientResponse],
    dependencies=[Depends(AdminHasPermission())],
    name="Update Client",
    description="Update client (Admin only)"
)
async def update_client(
    client_data: UpdateClientRequest,
    service: Annotated[ClientService, Depends()],
    user: Annotated[Users, Depends(AdminHasPermission())],
    client_id: str = Path(..., description="Client ID"),
) -> BaseResponse[UpdateClientResponse]:
    """
    Update an existing client.
    
    This endpoint requires admin permissions and updates the client with the provided data.
    If media information is provided, it will update or create the associated media record.
    
    Args:
        client_data: Client update data
        client_id: ID of the client to update
        service: ClientService instance for business logic
        user: Authenticated admin user
        
    Returns:
        BaseResponse with updated client ID and success message
        
    Raises:
        NotFoundError: If client not found
        ConflictError: If update would create conflicts
    """
    client = await service.update_client(client_id, client_data, user.id)
    
    return BaseResponse(
        data=UpdateClientResponse(
            id=client.id,
            message="Client updated successfully"
        )
    )


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[DeleteClientResponse],
    dependencies=[Depends(AdminHasPermission())],
    name="Delete Client",
    description="Delete client (Admin only)"
)
async def delete_client(
    service: Annotated[ClientService, Depends()],
    user: Annotated[Users, Depends(AdminHasPermission())],
    client_id: str = Path(..., description="Client ID"),
) -> BaseResponse[DeleteClientResponse]:
    """
    Delete a client.
    
    This endpoint requires admin permissions and performs a soft delete of the client.
    
    Args:
        client_id: ID of the client to delete
        service: ClientService instance for business logic
        user: Authenticated admin user
        
    Returns:
        BaseResponse with deleted client ID and success message
        
    Raises:
        NotFoundError: If client not found
    """
    await service.delete_client(client_id, user.id)
    
    return BaseResponse(
        data=DeleteClientResponse(
            id=client_id,
            message="Client deleted successfully"
        )
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[ClientListResponse],
    name="List Clients",
    description="List all clients with pagination and filters"
)
async def list_clients(
    service: Annotated[ClientService, Depends()],
    params: Annotated[ListClientsRequest, Depends()]
) -> BaseResponse[ClientListResponse]:
    """
    List all clients with filtering, searching, and pagination.
    
    Args:
        params: List parameters including filters and pagination
        service: ClientService instance for business logic
        
    Returns:
        BaseResponse with paginated list of clients
    
    Raises:
        NotFoundError: If client not found
    """
    clients = await service.list_clients(params=params)
    
    return BaseResponse(data=clients)