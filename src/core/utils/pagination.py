import math
from typing import Any, Dict, Generic, List, Optional, TypeVar

from fastapi import Query
from fastapi_pagination import Params
from pydantic import Field, conint
from sqlalchemy import Select, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from .schema import CamelCaseModel

T = TypeVar("T")


class PaginationParams:
    """Advanced pagination parameters with search, filtering, and sorting capabilities."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=1, le=100, description="Items per page"),
        search: Optional[str] = Query(None, description="Search term"),
        sort_by: Optional[str] = Query(None, description="Sort field"),
        sort_order: Optional[str] = Query(
            "desc", regex="^(asc|desc)$", description="Sort order (asc/desc)"
        ),
        filters: Optional[str] = Query(None, description="JSON string of filters"),
        date_from: Optional[str] = Query(
            None, description="Filter from date (ISO format)"
        ),
        date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    ):
        self.page = page
        self.page_size = page_size
        self.search = search
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.filters = self._parse_filters(filters)
        self.date_from = date_from
        self.date_to = date_to

    def _parse_filters(self, filters_str: Optional[str]) -> Dict[str, Any]:
        """Parse JSON filters string into dictionary."""
        if not filters_str:
            return {}
        try:
            import json

            return json.loads(filters_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def skip(self) -> int:
        """Calculate skip value for pagination."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit value for pagination."""
        return self.page_size

    @property
    def offset(self) -> int:
        """Alias for skip."""
        return self.skip

    def to_fastapi_pagination_params(self) -> Params:
        """Convert to fastapi-pagination Params."""
        return Params(page=self.page, size=self.page_size)


class PaginatedResponse(CamelCaseModel, Generic[T]):
    """Enhanced paginated response with metadata and navigation."""

    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: conint(ge=1) = Field(..., description="Current page number")
    page_size: conint(ge=1) = Field(..., description="Number of items per page")
    pages: conint(ge=1) = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    @classmethod
    def create(
        cls, items: List[T], total: int, params: PaginationParams
    ) -> "PaginatedResponse[T]":
        """Create a paginated response from items and parameters."""
        pages = math.ceil(total / params.page_size) if total > 0 else 1

        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
            has_next=params.page < pages,
            has_prev=params.page > 1,
        )


class PaginationQueryBuilder:
    """Advanced query builder for pagination with search, filtering, and sorting."""

    def __init__(self, base_query: Select, session: AsyncSession):
        self.base_query = base_query
        self.session = session
        self._query = base_query

    def apply_search(
        self, search: Optional[str], search_fields: List[str]
    ) -> "PaginationQueryBuilder":
        """Apply search across specified fields."""
        if not search or not search_fields:
            return self

        from sqlalchemy import func, or_

        # Get the model class from the query
        model_class = self.base_query.column_descriptions[0]["type"]

        search_conditions = []
        for field in search_fields:
            if hasattr(model_class, field):
                search_conditions.append(
                    func.lower(getattr(model_class, field)).contains(func.lower(search))
                )

        if search_conditions:
            self._query = self._query.where(or_(*search_conditions))

        return self

    def apply_filters(
        self, filters: Dict[str, Any], allowed_filters: List[str]
    ) -> "PaginationQueryBuilder":
        """Apply filters to the query."""
        if not filters:
            return self

        # Get the model class from the query
        model_class = self.base_query.column_descriptions[0]["type"]

        for field, value in filters.items():
            if field in allowed_filters and hasattr(model_class, field):
                if isinstance(value, (list, tuple)):
                    self._query = self._query.where(
                        getattr(model_class, field).in_(value)
                    )
                else:
                    self._query = self._query.where(
                        getattr(model_class, field) == value
                    )

        return self

    def apply_date_range(
        self, date_from: Optional[str], date_to: Optional[str], date_field: str
    ) -> "PaginationQueryBuilder":
        """Apply date range filtering."""
        # Get the model class from the query
        model_class = self.base_query.column_descriptions[0]["type"]

        if not (date_from or date_to) or not hasattr(model_class, date_field):
            return self

        from datetime import datetime

        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                self._query = self._query.where(
                    getattr(model_class, date_field) >= from_date
                )
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                self._query = self._query.where(
                    getattr(model_class, date_field) <= to_date
                )
            except ValueError:
                pass

        return self

    def apply_sorting(
        self, sort_by: Optional[str], sort_order: str, allowed_sort_fields: List[str]
    ) -> "PaginationQueryBuilder":
        """Apply sorting to the query."""
        if not sort_by or sort_by not in allowed_sort_fields:
            return self

        # Get the model class from the query
        model_class = self.base_query.column_descriptions[0]["type"]

        if hasattr(model_class, sort_by):
            field = getattr(model_class, sort_by)
            if sort_order.lower() == "desc":
                self._query = self._query.order_by(desc(field))
            else:
                self._query = self._query.order_by(asc(field))

        return self

    def get_query(self) -> Select:
        """Get the final query."""
        return self._query

    async def paginate(self, params: PaginationParams) -> PaginatedResponse[T]:
        """Execute paginated query and return results."""
        # Apply pagination
        paginated_query = self._query.offset(params.skip).limit(params.limit)

        # Execute queries
        result = await self.session.execute(paginated_query)
        items = result.scalars().all()

        # Get total count
        count_query = self._query.with_only_columns(func.count())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()

        return PaginatedResponse.create(items, total, params)


# Dependency functions for easy integration
def get_pagination_params() -> PaginationParams:
    """Dependency to get pagination parameters."""
    return PaginationParams()


def get_advanced_pagination_params(
    search_fields: Optional[List[str]] = None,
    allowed_filters: Optional[List[str]] = None,
    allowed_sort_fields: Optional[List[str]] = None,
    date_field: Optional[str] = None,
) -> PaginationParams:
    """Dependency factory for advanced pagination with field validation."""

    def _get_params() -> PaginationParams:
        """Get pagination parameters."""
        params = PaginationParams()

        # Validate sort_by if provided
        if (
            params.sort_by
            and allowed_sort_fields
            and params.sort_by not in allowed_sort_fields
        ):
            params.sort_by = None

        # Validate filters if provided
        if params.filters and allowed_filters:
            invalid_filters = [
                k for k in params.filters.keys() if k not in allowed_filters
            ]
            for invalid_filter in invalid_filters:
                params.filters.pop(invalid_filter, None)

        return params

    return _get_params


# Utility functions for common pagination patterns
async def paginate_query(
    query: Select,
    session: AsyncSession,
    params: PaginationParams,
    search_fields: Optional[List[str]] = None,
    allowed_filters: Optional[List[str]] = None,
    allowed_sort_fields: Optional[List[str]] = None,
    date_field: Optional[str] = None,
) -> PaginatedResponse[T]:
    """Utility function to paginate any SQLAlchemy query with advanced features."""

    builder = PaginationQueryBuilder(query, session)

    if search_fields:
        builder.apply_search(params.search, search_fields)

    if allowed_filters:
        builder.apply_filters(params.filters, allowed_filters)

    if date_field:
        builder.apply_date_range(params.date_from, params.date_to, date_field)

    if allowed_sort_fields:
        builder.apply_sorting(params.sort_by, params.sort_order, allowed_sort_fields)

    return await builder.paginate(params)
