from slugify import slugify
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import AlreadyExistsError


async def get_existing_slugs(
    base_slug: str,
    db: Session,
    model: type,
    existing_id: str | None = None,
) -> set[str]:
    """
    Fetch all existing slugs that match the base slug pattern from the database.

    Args:
        base_slug (str): The base slug to check for existing variations.
        db (Session): The database session.
        model (type): The SQLAlchemy model containing the slug field.

    Returns:
        set[str]: A set of existing slugs matching the base slug.
    """
    stmt = select(model.slug).where(
        model.slug.like(f"{base_slug}%"), model.deleted_at.is_(None)
    )

    if existing_id:
        stmt = stmt.where(model.id != existing_id)

    result = await db.execute(stmt)
    return set(result.scalars().all())  # Convert to a set for quick lookup


async def generate_unique_slug(
    text: str,
    db: Session,
    model: type,
    existing_id: str | None = None,
) -> str:
    """
    Generate a unique slug from the given text, ensuring no duplication in the database.

    Args:
        text (str): The input string to convert into a slug.
        db (Session): The database session.
        model (type): The SQLAlchemy model containing the slug field.

    Returns:
        str: A unique slug.
    """
    base_slug = slugify(text)
    existing_slugs = await get_existing_slugs(
        base_slug, db, model, existing_id
    )

    unique_slug = base_slug
    count = 1
    while unique_slug in existing_slugs:
        unique_slug = f"{base_slug}-{count}"
        count += 1

    return unique_slug


async def validate_unique_slug(
    slug: str,
    db: Session,
    model: type,
) -> set[str]:
    """
    Check if the given slug already exists in the database.

    Args:
        slug (str): The base slug to check for existing variations.
        db (AsyncSession): The async database session.
        model (type): The SQLAlchemy model containing the slug field.

    Raises:
        ValueError: If the slug already exists.
    """
    stmt = select(model.slug).where(model.slug == slug, model.deleted_at.is_(None))

    result = await db.execute(stmt)
    existing_slug = result.scalar()

    if existing_slug:
        error_message = f"Slug '{slug}' already exists."
        raise AlreadyExistsError(error_message)


async def validate_and_generate_slug(
    name: str,
    db: Session,
    model: type,
    slug: str | None,
) -> str:
    """
    Validate an existing slug (if provided) and generate a unique one if needed.

    Args:
        slug (str | None): The slug provided by the user, if any.
        name (str): The name to generate a slug from if no slug is provided.
        db (AsyncSession): The async database session.
        model (type): The SQLAlchemy model containing the slug field.

    Returns:
        str: A validated or newly generated unique slug.
    """

    # If a slug is provided, validate it
    if slug:
        await validate_unique_slug(
            slug,
            db=db,
            model=model,
        )
        return slug  # If valid, return it immediately

    # Otherwise, generate a unique slug from the name
    return await generate_unique_slug(
        name, db=db, model=model
    )
