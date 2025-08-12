from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Body, Depends, status

from media.schemas import (
    CreateRequest,
    UpdateRequest,
    SampleResponse,
)
from media.services import mediaService
from media.models import mediaModel

router = APIRouter(prefix="/api/v1/media", tags=["media"])

# Create your routes here

