from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from apps.clients.schemas.request import (
    CreateClientRequest,
    ListClientsRequest,
    UpdateClientRequest,
)
from apps.clients.schemas.response import (
    ClientListResponse,
    ClientResponse,
    ClientStatusResponse,
    CreateClientResponse,
    GlobalClientResponse,
    UpdateClientResponse,
)
from apps.clients.services.clients import ClientService
from apps.users.models.user import Users
from apps.users.utils import current_user, permission_required
from apps.clients.constants import ClientMessage
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponse[CreateClientResponse],
    name="Create Client",
    description="Create a new client (Access token required)",
    dependencies=[Depends(permission_required(["clients"], ["client-management"]))],
)
async def create_client(
    client_data: CreateClientRequest,
    service: Annotated[ClientService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[CreateClientResponse]:
    """
    Create a new client.

    This endpoint requires access token and creates a new client with the provided data.
    If media information is provided, it will also create the associated media record.

    Args:
        client_data: Client creation data including name, code, and optional media
        service: ClientService instance for business logic
        user: Access token claims containing client context

    Returns:
        BaseResponse with created client ID and success message

    Raises:
        ConflictError: If client with same name or code already exists
    """
    client = await service.create_client(client_data, user.get("user").id)

    return BaseResponse(
        data=CreateClientResponse(
            id=str(client.id), message=ClientMessage.CLIENT_CREATED
        )
    )


@router.get(
    "/{client_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[ClientResponse],
    name="Get Client",
    description="Get client by ID (Access token required)",
    dependencies=[Depends(permission_required(["clients"], ["client-management"]))],
)
async def get_client(
    service: Annotated[ClientService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
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


@router.get(
    "/global/clients",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[list[GlobalClientResponse]],
    name="Get global clients",
    description="Get global clients",
)
async def get_global_clients(
    service: Annotated[ClientService, Depends()]
) -> BaseResponse[list[GlobalClientResponse]]:
    """
    Get global clients
    """
    return BaseResponse(data=await service.get_global_clients())


@router.put(
    "/{client_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[UpdateClientResponse],
    name="Update Client",
    description="Update client (Access token required)",
    dependencies=[Depends(permission_required(["clients"], ["client-management"]))],
)
async def update_client(
    client_data: UpdateClientRequest,
    service: Annotated[ClientService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
    client_id: str = Path(..., description="Client ID"),
) -> BaseResponse[UpdateClientResponse]:
    """
    Update an existing client.

    This endpoint requires access token and updates the client with the provided data.
    If media information is provided, it will update or create the associated media record.

    Args:
        client_data: Client update data
        client_id: ID of the client to update
        service: ClientService instance for business logic
        user: Access token claims containing client context

    Returns:
        BaseResponse with updated client ID and success message

    Raises:
        NotFoundError: If client not found
        ConflictError: If update would create conflicts
    """
    client = await service.update_client(client_id, client_data, user.get("user").id)

    return BaseResponse(
        data=UpdateClientResponse(id=client.id, message=ClientMessage.CLIENT_UPDATED)
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[ClientListResponse],
    name="List Clients",
    description="List all clients with pagination and filters (returns only id, name, and code)",
    dependencies=[Depends(permission_required(["clients"], ["client-management"]))],
)
async def list_clients(
    service: Annotated[ClientService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
    params: Annotated[ListClientsRequest, Depends()],
) -> BaseResponse[ClientListResponse]:
    """
    List all clients with filtering, searching, and pagination.
    Returns only id, name, and code for each client.

    Args:
        params: List parameters including filters and pagination
        service: ClientService instance for business logic

    Returns:
        BaseResponse with paginated list of clients (id, name, code only)

    Raises:
        NotFoundError: If client not found
    """
    clients = await service.list_clients(params=params)

    return BaseResponse(data=clients)


@router.patch(
    "/{client_id}/status",
    name="Make client active/Inactive",
    operation_id="change-client-status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(permission_required(["clients"], ["client-management"]))],
)
async def change_client_status(
    user: Annotated[tuple[Users, str], Depends(current_user)],
    client_id: Annotated[str, Path()],
    service: Annotated[ClientService, Depends()],
) -> BaseResponse[ClientStatusResponse]:
    """
    Toggles the active status of a client by their ID.

    Args:
        - client_id (str): The ID of the client whose status is to be changed.

    Returns:
        - BaseResponse[ClientStatusResponse]: A response indicating
        the client's updated status.

    Raises:
        - ClientNotFoundError: If no client with the provided ID is found.

    """

    return BaseResponse(
        data=await service.change_client_status(client_id=client_id, current_user_id=user.get("user").id)
    )
