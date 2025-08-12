from typing import Annotated
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import Depends

from apps.media.schemas.response import MediaResponse
from core.db import db_session
from core.exceptions import NotFoundError, ConflictError
from apps.clients.models.clients import Clients
from apps.media.models.media import Media
from apps.clients.schemas.request import CreateClientRequest, UpdateClientRequest, ListClientsRequest
from apps.clients.schemas.response import ClientResponse, ClientListResponse
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Params


class ClientService:
    """Service for managing client operations."""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Initialize the service with database session."""
        self.session = session

    async def create_client(self, client_data: CreateClientRequest, user_id: str) -> Clients:
        """
        Create a new client.
        
        Args:
            client_data: Client creation data
            user_id: ID of the user creating the client
            
        Returns:
            Created client instance
            
        Raises:
            ConflictError: If client with same name, code, or slug already exists
        """
        # Check for existing client with same name, code, or slug
        existing_client = await self.session.scalar(
            select(Clients).where(
                or_(
                    Clients.name == client_data.name,
                    Clients.code == client_data.code,
                    Clients.slug == client_data.slug
                )
            )
        )
        
        if existing_client:
            if existing_client.name == client_data.name:
                raise ConflictError(message=f"Client with name '{client_data.name}' already exists")
            elif existing_client.code == client_data.code:
                raise ConflictError(message=f"Client with code '{client_data.code}' already exists")
            else:
                raise ConflictError(message=f"Client with slug '{client_data.slug}' already exists")

        # Create media if provided
        media_id = None
        if client_data.media:
            media = Media(
                file_name=client_data.media.file_name,
                file_path=client_data.media.file_path,
                file_type=client_data.media.file_type
            )
            self.session.add(media)
            media_id = media.id

        # Create client
        client = Clients(
            name=client_data.name,
            code=client_data.code,
            slug=client_data.slug,
            description=client_data.description,
            meta_data=client_data.meta_data,
            media_id=media_id,
            is_active=client_data.is_active,
            created_by=user_id,
            updated_by=user_id
        )
        
        self.session.add(client)
        
        return client

    async def get_client_by_id(self, client_id: str) -> Clients:
        """
        Get a client by ID.
        
        Args:
            client_id: ID of the client to retrieve
            
        Returns:
            Client instance
            
        Raises:
            NotFoundError: If client not found
        """
        client = await self.session.scalar(
            select(Clients)
            .options(selectinload(Clients.media))
            .where(Clients.id == client_id)
        )
        
        if not client:
            raise NotFoundError(message=f"Client with ID '{client_id}' not found")
        
        return client

    async def update_client(self, client_id: str, client_data: UpdateClientRequest, user_id: str) -> Clients:
        """
        Update an existing client.
        
        Args:
            client_id: ID of the client to update
            client_data: Client update data
            user_id: ID of the user updating the client
            
        Returns:
            Updated client instance
            
        Raises:
            NotFoundError: If client not found
            ConflictError: If update would create conflicts
        """
        client = await self.get_client_by_id(client_id)
        
        # Check for conflicts if updating unique fields
        if client_data.name and client_data.name != client.name:
            existing = await self.session.scalar(
                select(Clients).where(
                    and_(Clients.name == client_data.name, Clients.id != client_id)
                )
            )
            if existing:
                raise ConflictError(message=f"Client with name '{client_data.name}' already exists")
        
        if client_data.code and client_data.code != client.code:
            existing = await self.session.scalar(
                select(Clients).where(
                    and_(Clients.code == client_data.code, Clients.id != client_id)
                )
            )
            if existing:
                raise ConflictError(message=f"Client with code '{client_data.code}' already exists")
        
        if client_data.slug and client_data.slug != client.slug:
            existing = await self.session.scalar(
                select(Clients).where(
                    and_(Clients.slug == client_data.slug, Clients.id != client_id)
                )
            )
            if existing:
                raise ConflictError(message=f"Client with slug '{client_data.slug}' already exists")

        # Update media if provided
        if client_data.media:
            if client.media_id:
                # Update existing media
                media = await self.session.get(Media, client.media_id)
                if media:
                    media.file_name = client_data.media.file_name
                    media.file_path = client_data.media.file_path
                    media.file_type = client_data.media.file_type
            else:
                # Create new media
                media = Media(
                    file_name=client_data.media.file_name,
                    file_path=client_data.media.file_path,
                    file_type=client_data.media.file_type
                )
                self.session.add(media)
                client.media_id = media.id

        # Update client fields
        if client_data.name is not None:
            client.name = client_data.name
        if client_data.code is not None:
            client.code = client_data.code
        if client_data.slug is not None:
            client.slug = client_data.slug
        if client_data.description is not None:
            client.description = client_data.description
        if client_data.meta_data is not None:
            client.meta_data = client_data.meta_data
        if client_data.is_active is not None:
            client.is_active = client_data.is_active
        
        client.updated_by = user_id
        
        return client

    async def delete_client(self, client_id: str, user_id: str) -> bool:
        """
        Delete a client.
        
        Args:
            client_id: ID of the client to delete
            user_id: ID of the user deleting the client
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If client not found
        """
        client = await self.get_client_by_id(client_id)
        
        # Soft delete the client
        client.deleted_at = func.now()
        client.deleted_by = user_id
                
        return True

    async def list_clients(self, params: ListClientsRequest) -> ClientListResponse:
        """
        List clients with filtering, searching, and pagination.
        
        Args:
            params: List parameters including filters and pagination
            
        Returns:
            Paginated list of clients
        """
        query = select(Clients).options(selectinload(Clients.media))
        
        # Apply filters
        if params.is_active is not None:
            query = query.where(Clients.is_active == params.is_active)
        
        # Apply search
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    Clients.name.ilike(search_term),
                    Clients.code.ilike(search_term),
                    Clients.description.ilike(search_term)
                )
            )
        
        # Apply sorting
        if params.sort_by:
            sort_field = getattr(Clients, params.sort_by, Clients.created_at)
            if params.sort_order.lower() == "desc":
                query = query.order_by(sort_field.desc())
            else:
                query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(Clients.created_at.desc())
        
        # Apply pagination
        pagination_params = Params(page=params.page, size=params.page_size)
        result = await paginate(self.session, query, pagination_params)
        
        return ClientListResponse(
            items=[self._to_response(client) for client in result.items],
            total=result.total,
            page=result.page,
            page_size=result.size,
            pages=result.pages
        )

    def _to_response(self, client: Clients) -> ClientResponse:
        """Convert client model to response schema."""
        return ClientResponse(
            id=client.id,
            name=client.name,
            code=client.code,
            slug=client.slug,
            description=client.description,
            meta_data=client.meta_data,
            media=MediaResponse(
                id=client.media.id,
                file_name=client.media.file_name,
                file_path=client.media.file_path,
                file_type=client.media.file_type,
                created_at=client.media.created_at,
                updated_at=client.media.updated_at
            ) if client.media else None,
            is_active=client.is_active,
            created_at=client.created_at,
            updated_at=client.updated_at,
            created_by=client.created_by,
            updated_by=client.updated_by
        )
