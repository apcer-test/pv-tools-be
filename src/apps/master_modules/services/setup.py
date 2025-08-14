from typing import Annotated

import pandas as pd
from fastapi import Depends, UploadFile
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

import constants
from apps.master_modules.exception import (
    EmptyExcelFileException,
    ExistingLookupValueException,
    InvalidExcelSheetDataException,
    InvalidFileFormatException,
    InvalidRequestException,
    LookupNotFoundException,
    LookupValueNotFoundException,
)
from apps.master_modules.models.setup import LookupModel, LookupValuesModel
from apps.master_modules.schemas.response import (
    CodeListLookupValueResponse,
    LookupResponse,
    NFListLookupValueResponse,
)
from core.common_helpers import compute_batch_size
from core.db import db_session
from core.types import LookupType
from core.utils import logger
from core.utils.pagination import PaginatedResponse, PaginationParams, paginate_query
from core.utils.schema import SuccessResponse


class SetupService:
    """
    Service class for handling setup operations.

    This service provides methods for processing Excel files to create and manage lookup entries.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize SetupService with a database session.

        Args:
            session (AsyncSession): An asynchronous database session.
        """
        self.session = session

    async def process_excel_file(self, file: UploadFile) -> SuccessResponse:
        """
        Process the uploaded Excel file and create lookup entries.

        The Excel file must contain two sheets:
        1. 'Lookup' - Contains lookup model definitions with columns: Name, Slug, Type
        2. 'Lookup Values' - Contains lookup values with columns: Slug (reference to Lookup), Name, R2 Code, R3 Code

        Args:
            file (UploadFile): The uploaded Excel file containing lookup data.

        Returns:
            Dict: A dictionary containing processing results including counts of created entries.

        Raises:
            HTTPException: If file format is invalid, required sheets/columns are missing, or processing fails.
        """
        if not file.filename.endswith(tuple(constants.ALLOWED_FILE_EXTENSIONS)):
            logger.info(f"Invalid file format: {file.filename}")
            raise InvalidFileFormatException

        try:
            # Read both sheets from the Excel file
            excel_file = pd.ExcelFile(file.file)
            required_sheets = constants.REQUIRED_EXCEL_SHEET_NAMES

            if not set(required_sheets).issubset(set(excel_file.sheet_names)):
                raise InvalidExcelSheetDataException

            # Read Lookup sheet
            lookup_df = pd.read_excel(
                excel_file, sheet_name="Lookup", keep_default_na=False
            )
            required_lookup_columns = constants.REQUIRED_LOOKUP_SHEET_COLUMNS

            if not set(required_lookup_columns).issubset(set(lookup_df.columns)):
                logger.info(f"Invalid lookup sheet data: {lookup_df.columns}")
                raise InvalidExcelSheetDataException

            # Read Lookup Values sheet
            values_df = pd.read_excel(
                excel_file, sheet_name="Lookup Values", keep_default_na=False
            )
            required_values_columns = constants.REQUIRED_LOOKUP_VALUES_SHEET_COLUMNS

            if not set(required_values_columns).issubset(set(values_df.columns)):
                logger.info(f"Invalid lookup values sheet data: {values_df.columns}")
                raise InvalidExcelSheetDataException

            # Validate mandatory fields in each row for both sheets
            def _is_blank(cell: object) -> bool:
                """Check if a cell is blank."""
                try:
                    if cell is None or pd.isna(cell):
                        return True
                except Exception:
                    # pd.isna may raise on some types; treat as not blank
                    pass
                if isinstance(cell, str):
                    # treat literal strings like 'None', 'N/A' as data, not blank
                    if cell.strip() == "":
                        return True
                    return False
                return False

            # Lookup sheet: Name, Slug, Lookup Type are mandatory
            missing_any = False
            for idx, row in lookup_df.iterrows():
                missing_cols: list[str] = []
                if _is_blank(row.get("Name")):
                    missing_cols.append("Name")
                if _is_blank(row.get("Slug")):
                    missing_cols.append("Slug")
                if _is_blank(row.get("Lookup Type")):
                    missing_cols.append("Lookup Type")
                if missing_cols:
                    missing_any = True
                    logger.info(
                        f"Lookup sheet missing required fields at row {idx + 2}: {', '.join(missing_cols)}"
                    )

            # Lookup Values sheet: Slug, Value are mandatory
            for idx, row in values_df.iterrows():
                missing_cols: list[str] = []
                if _is_blank(row.get("Slug")):
                    missing_cols.append("Slug")
                if _is_blank(row.get("Value")):
                    missing_cols.append("Value")
                if missing_cols:
                    missing_any = True
                    logger.info(
                        f"Lookup Values sheet missing required fields at row {idx + 2}: {', '.join(missing_cols)}"
                    )

            if missing_any:
                raise InvalidExcelSheetDataException

            lookup_map: dict[str, str] = {}  # slug -> lookup_id

            # Build rows for bulk upsert into LookupModel with de-duplication by slug
            lookup_rows_map: dict[str, dict] = {}
            for _, row in lookup_df.iterrows():
                if pd.isna(row["Name"]) or pd.isna(row["Slug"]):
                    continue
                slug_value = str(row["Slug"]).strip()
                if not slug_value:
                    continue
                lookup_rows_map[slug_value] = {
                    "name": row["Name"],
                    "slug": slug_value,
                    "lookup_type": (
                        None if pd.isna(row["Lookup Type"]) else row["Lookup Type"]
                    ),
                    "is_active": True,
                }
            lookup_rows: list[dict] = list(lookup_rows_map.values())

            if lookup_rows:
                # Batch upsert to avoid asyncpg 32767 parameter limit
                insert_lookup = pg_insert(LookupModel)
                batch_size = compute_batch_size(len(lookup_rows[0]))
                for i in range(0, len(lookup_rows), batch_size):
                    batch = lookup_rows[i : i + batch_size]
                    stmt = insert_lookup.values(batch)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["slug"],
                        set_={
                            "name": stmt.excluded.name,
                            "slug": stmt.excluded.slug,
                            "lookup_type": stmt.excluded.lookup_type,
                            "is_active": True,
                        },
                    ).returning(LookupModel.id, LookupModel.slug)
                    result = await self.session.execute(stmt)
                    rows = result.all()
                    lookup_map.update({slug: _id for (_id, slug) in rows})

            # Ensure we have lookup ids for any slugs that only appear in Values sheet
            slugs_in_values = set(values_df["Slug"].dropna().astype(str).tolist())
            missing_slugs = slugs_in_values.difference(set(lookup_map.keys()))
            if missing_slugs:
                result = await self.session.execute(
                    select(LookupModel.slug, LookupModel.id).where(
                        LookupModel.slug.in_(list(missing_slugs))
                    )
                )
                for slug, _id in result.all():
                    lookup_map[slug] = _id

            # Build rows for bulk upsert into LookupValuesModel with de-duplication by (lookup_model_id, name)
            value_rows_map: dict[tuple[str, str], dict] = {}
            for _, row in values_df.iterrows():
                if pd.isna(row["Value"]) or pd.isna(row["Slug"]):
                    continue
                slug_value = str(row["Slug"]).strip()
                if not slug_value:
                    continue
                lookup_id = lookup_map.get(slug_value)
                if not lookup_id:
                    continue
                value_name = str(row["Value"]).strip()
                key = (lookup_id, value_name)
                value_rows_map[key] = {
                    "lookup_model_id": lookup_id,
                    "name": value_name,
                    "e2b_code_r2": (
                        None if pd.isna(row["E2B Code R2"]) else row["E2B Code R2"]
                    ),
                    "e2b_code_r3": (
                        None if pd.isna(row["E2B Code R3"]) else row["E2B Code R3"]
                    ),
                    "is_active": True,
                }
            value_rows: list[dict] = list(value_rows_map.values())

            if value_rows:
                # Batch upsert to avoid asyncpg 32767 parameter limit

                insert_values = pg_insert(LookupValuesModel)
                batch_size = compute_batch_size(len(value_rows[0]))
                for i in range(0, len(value_rows), batch_size):
                    batch = value_rows[i : i + batch_size]
                    stmt = insert_values.values(batch)
                    stmt = stmt.on_conflict_do_update(
                        constraint="uq_lookup_model_name",
                        set_={
                            "e2b_code_r2": stmt.excluded.e2b_code_r2,
                            "e2b_code_r3": stmt.excluded.e2b_code_r3,
                            "is_active": True,
                        },
                    )
                    await self.session.execute(stmt)

            return SuccessResponse(message=constants.EXCEL_FILE_PROCESSED_SUCCESSFULLY)

        except pd.errors.EmptyDataError:
            raise EmptyExcelFileException
        except Exception:
            await self.session.rollback()
            raise InvalidExcelSheetDataException
        finally:
            file.file.close()

    async def get_codelist_lookup_list(
        self,
        is_active: bool | None = None,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[LookupResponse]:
        """
        Get list of all code-list lookup entries.

        Returns:
            LookupListResponse: List of lookup entries with id, name, slug and type.
        """
        # Query active code-list lookup entries
        stmt = select(LookupModel).where(LookupModel.lookup_type == LookupType.CODELIST.value).order_by(LookupModel.updated_at.desc())
        if is_active is not None:
            stmt = stmt.where(LookupModel.is_active == is_active)
        assert params is not None, "Pagination params must be provided"

        # Apply search on name field if provided
        if params.search:
            search_term = func.lower(params.search)
            stmt = stmt.where(
                func.lower(LookupModel.name).contains(search_term)
                | func.lower(LookupModel.slug).contains(search_term)
            )

        # Order by latest updated and paginate using helper to also compute total
        page = await paginate_query(
            stmt,
            self.session,
            params,
            default_sort_by="updated_at",
            default_sort_order="desc",
        )

        # Map to response models while reusing total from paginator
        lookup_responses: list[LookupResponse] = []
        for lookup in page.items:
            lookup_responses.append(
                LookupResponse(
                    id=str(lookup.id),
                    name=lookup.name,
                    slug=lookup.slug,
                )
            )

        return PaginatedResponse.create(
            items=lookup_responses, total=page.total, params=params
        )

    async def get_nflist_lookup_list(
        self,
        is_active: bool | None = None,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[LookupResponse]:
        """
        Get list of all nf-list lookup entries.

        Returns:
            LookupListResponse: List of lookup entries with id, name, slug and type.
        """
        # Query active nf-list lookup entries
        stmt = select(LookupModel).where(LookupModel.lookup_type == LookupType.NFLIST.value).order_by(LookupModel.updated_at.desc())
        if is_active is not None:
            stmt = stmt.where(LookupModel.is_active == is_active)
        assert params is not None, "Pagination params must be provided"

        # Apply search on name field if provided
        if params.search:
            search_term = func.lower(params.search)
            stmt = stmt.where(
                func.lower(LookupModel.name).contains(search_term)
                | func.lower(LookupModel.slug).contains(search_term)
            )

        # Order by latest updated and paginate using helper to also compute total
        page = await paginate_query(
            stmt,
            self.session,
            params,
            default_sort_by="updated_at",
            default_sort_order="desc",
        )

        # Map to response models while reusing total from paginator
        lookup_responses: list[LookupResponse] = []
        for lookup in page.items:
            lookup_responses.append(
                LookupResponse(
                    id=str(lookup.id),
                    name=lookup.name,
                    slug=lookup.slug,
                )
            )

        return PaginatedResponse.create(
            items=lookup_responses, total=page.total, params=params
        )

    async def get_lookup_values(
        self, lookup_id: str, params: PaginationParams, is_active: bool | None = None
    ) -> (
        PaginatedResponse[CodeListLookupValueResponse]
        | PaginatedResponse[NFListLookupValueResponse]
    ):
        """
        Get paginated lookup values for a specific lookup id.
        Returns response shape inferred from the lookup type.
        """
        # Validate that lookup exists
        lookup = await self.session.scalar(
            select(LookupModel).where((LookupModel.id == lookup_id))
        )
        if not lookup:
            # Hide details, return empty list
            empty = []
            return PaginatedResponse.create(items=empty, total=0, params=params)

        # Build values query
        stmt = select(LookupValuesModel).where(
            (LookupValuesModel.lookup_model_id == lookup_id)
        )
        if is_active is not None:
            stmt = stmt.where(LookupValuesModel.is_active == is_active)
        # Determine search fields per lookup type and paginate via helper

        ordered_stmt = stmt.order_by(LookupValuesModel.updated_at.desc())
        page = await paginate_query(
            ordered_stmt,
            self.session,
            params,
            search_fields=["name"],
            default_sort_by="updated_at",
            default_sort_order="desc",
        )
        values = page.items

        # Map based on type
        if lookup.lookup_type == LookupType.NFLIST.value:
            items: list[NFListLookupValueResponse] = []
            for v in values:
                items.append(
                    NFListLookupValueResponse(
                        id=str(v.id), name=v.name, is_active=v.is_active
                    )
                )
            return PaginatedResponse.create(
                items=items, total=page.total, params=params
            )
        else:
            items2: list[CodeListLookupValueResponse] = []
            for v in values:
                items2.append(
                    CodeListLookupValueResponse(
                        id=str(v.id),
                        name=v.name,
                        e2b_code_r2=v.e2b_code_r2,
                        e2b_code_r3=v.e2b_code_r3,
                        is_active=v.is_active,
                    )
                )
            return PaginatedResponse.create(
                items=items2, total=page.total, params=params
            )

    async def verify_lookup_value_exists(self, lookup_id: str, name: str) -> bool:
        """Verify if a lookup value exists for a given lookup id and name."""
        return await self.session.scalar(
            select(LookupValuesModel).where(
                (LookupValuesModel.lookup_model_id == lookup_id)
                & (LookupValuesModel.name == name)
            )
        )

    async def create_codelist_lookup_value(
        self,
        lookup_id: str,
        name: str,
        e2b_code_r2: str | None = None,
        e2b_code_r3: str | None = None,
    ) -> SuccessResponse:
        """Create a lookup value for a code-list lookup. Sets is_active=True."""
        # Validate lookup exists and is of code-list type if type is set
        lookup = await self.session.scalar(
            select(LookupModel).where(
                (LookupModel.id == lookup_id)
                & (LookupModel.lookup_type == LookupType.CODELIST.value)
            )
        )
        if not lookup:
            raise LookupNotFoundException

        existing_lookup_value = await self.verify_lookup_value_exists(lookup_id, name)
        if existing_lookup_value:
            raise ExistingLookupValueException

        # Create value
        value = LookupValuesModel(
            lookup_model_id=lookup_id,
            name=name,
            e2b_code_r2=e2b_code_r2,
            e2b_code_r3=e2b_code_r3,
            is_active=True,
        )
        self.session.add(value)

        return SuccessResponse(message=constants.LOOKUP_VALUE_CREATED_SUCCESSFULLY)

    async def create_nflist_lookup_value(
        self, lookup_id: str, name: str
    ) -> SuccessResponse:
        """Create a lookup value for an nf-list lookup. Sets is_active=True."""
        lookup = await self.session.scalar(
            select(LookupModel).where(
                (LookupModel.id == lookup_id)
                & (LookupModel.lookup_type == LookupType.NFLIST.value)
            )
        )
        if not lookup:
            raise LookupNotFoundException

        existing_lookup_value = await self.verify_lookup_value_exists(lookup_id, name)

        if existing_lookup_value:
            raise ExistingLookupValueException

        value = LookupValuesModel(lookup_model_id=lookup_id, name=name, is_active=True)
        self.session.add(value)

        return SuccessResponse(message=constants.LOOKUP_VALUE_CREATED_SUCCESSFULLY)

    def _apply_lookup_value_updates(
        self,
        value: LookupValuesModel,
        name: str | None = None,
        is_active: bool | None = None,
        is_nflist: bool = False,
        e2b_code_r2: str | None = None,
        e2b_code_r3: str | None = None,
    ):
        """Apply updates to a lookup value."""
        if name is not None:
            value.name = name
        if is_active is not None:
            value.is_active = is_active
        if not is_nflist:
            if e2b_code_r2 is not None:
                value.e2b_code_r2 = e2b_code_r2
            if e2b_code_r3 is not None:
                value.e2b_code_r3 = e2b_code_r3

    async def update_lookup_value(
        self,
        lookup_value_id: str,
        name: str | None = None,
        e2b_code_r2: str | None = None,
        e2b_code_r3: str | None = None,
        is_active: bool | None = None,
    ) -> SuccessResponse:
        """
        Partially update a lookup value. All provided fields will be updated.
        - For nf-list values: only `name` and `is_active` are allowed.
        - For code-list values: `name`, `is_active`, `e2b_code_r2`, `e2b_code_r3` are allowed.
        """
        # Fetch value with its lookup type
        value = await self.session.scalar(
            select(LookupValuesModel)
            .options(
                load_only(
                    LookupValuesModel.id,
                    LookupValuesModel.lookup_model_id,
                    LookupValuesModel.name,
                    LookupValuesModel.e2b_code_r2,
                    LookupValuesModel.e2b_code_r3,
                    LookupValuesModel.is_active,
                )
            )
            .where(LookupValuesModel.id == lookup_value_id)
        )
        if not value:
            raise LookupValueNotFoundException

        lookup = await self.session.scalar(
            select(LookupModel)
            .options(load_only(LookupModel.id, LookupModel.lookup_type))
            .where(LookupModel.id == value.lookup_model_id)
        )
        if not lookup:
            raise LookupNotFoundException

        is_nflist = lookup.lookup_type == LookupType.NFLIST.value

        # Validate fields per type: if nf-list, reject e2b codes
        if is_nflist and (e2b_code_r2 is not None or e2b_code_r3 is not None):

            raise InvalidRequestException(message=constants.INVALID_NF_UPDATE_REQUEST)

        # If name is changing, ensure uniqueness within same lookup
        if name is not None and name.strip() and name != value.name:
            exists = await self.session.scalar(
                select(LookupValuesModel).where(
                    (LookupValuesModel.lookup_model_id == value.lookup_model_id)
                    & (LookupValuesModel.name == name)
                    & (LookupValuesModel.id != value.id)
                )
            )
            if exists:

                raise ExistingLookupValueException

        # Apply updates for provided fields only
        self._apply_lookup_value_updates(
            value, name, is_active, is_nflist, e2b_code_r2, e2b_code_r3
        )

        return SuccessResponse(message=constants.LOOKUP_VALUE_UPDATED_SUCCESSFULLY)

    async def update_lookup_status(
        self, lookup_id: str, is_active: bool
    ) -> SuccessResponse:
        """Update is_active for a lookup using the lookup id."""
        lookup = await self.session.scalar(
            select(LookupModel)
            .options(load_only(LookupModel.id, LookupModel.is_active))
            .where(LookupModel.id == lookup_id)
        )
        if not lookup:
            raise LookupNotFoundException

        lookup.is_active = is_active

        return SuccessResponse(message=constants.LOOKUP_STATUS_UPDATED_SUCCESSFULLY)

    async def get_lookup_values_by_slugs(
        self, slugs: list[str]
    ) -> dict[str, list[dict]]:
        """
        Fetch lookup values grouped by slug.

        For each slug provided, attempts to find an active lookup and returns all its values.
        If a slug is not found, an empty list is returned for that slug without raising an error.

        Returns a mapping of slug -> list of value dicts with keys: value, e2b_code_r2, e2b_code_r3, is_active.
        """
        # Preserve order while de-duplicating and trimming
        unique_slugs: list[str] = []
        seen: set[str] = set()
        for raw in slugs or []:
            if not isinstance(raw, str):
                continue
            s = raw.strip()
            if not s or s in seen:
                continue
            seen.add(s)
            unique_slugs.append(s)

        # Initialize with empty lists for all requested slugs
        slug_to_values: dict[str, list[dict]] = {slug: [] for slug in unique_slugs}

        if not unique_slugs:
            return slug_to_values

        # Fetch active lookups for slugs
        lookups_result = await self.session.execute(
            select(LookupModel.id, LookupModel.slug).where(
                (LookupModel.slug.in_(unique_slugs))
            )
        )
        lookup_rows = lookups_result.all()
        if not lookup_rows:
            return slug_to_values

        lookup_id_by_slug: dict[str, str] = {slug: _id for _id, slug in lookup_rows}
        lookup_ids = list(lookup_id_by_slug.values())

        # Fetch all values for these lookups
        values_result = await self.session.execute(
            select(
                LookupValuesModel.lookup_model_id,
                LookupValuesModel.name,
                LookupValuesModel.e2b_code_r2,
                LookupValuesModel.e2b_code_r3,
                LookupValuesModel.is_active,
            )
            .where(LookupValuesModel.lookup_model_id.in_(lookup_ids))
            .order_by(LookupValuesModel.updated_at.desc())
        )

        # Build reverse map from lookup_id to slug
        slug_by_lookup_id: dict[str, str] = {
            lookup_id: slug for slug, lookup_id in lookup_id_by_slug.items()
        }

        for lookup_model_id, name, r2, r3, is_active in values_result.all():
            slug = slug_by_lookup_id.get(lookup_model_id)
            if not slug:
                continue
            slug_to_values[slug].append(
                {
                    "value": name,
                    "e2b_code_r2": r2 or "",
                    "e2b_code_r3": r3 or "",
                    "is_active": bool(is_active),
                }
            )

        return slug_to_values
