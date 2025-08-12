import json
from typing import Annotated, List
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

import constants
from apps.media.models import mediaModel
from apps.media.schemas import (CreateRequest, UpdateRequest, SampleResponse)

from core.db import db_session




class mediaService:
    """
    Service with methods to handle media authentication and information.

    This service provides methods for creating media, logging in, and retrieving media information.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize mediaService with a database session
        This method also calls a database connection which is injected here.

        Args:
            session (AsyncSession): An asynchronous database connection.
        """
        self.session = session

    #create your services here 

