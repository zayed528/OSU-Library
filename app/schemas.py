"""Application data schemas.

This module contains small data schemas used by the app. It intentionally
keeps Pydantic models and simple dataclasses separate: dataclasses are
handy for small local utilities (seeding, fixtures) while Pydantic models are
used for request/response validation in the FastAPI routes.

Keep secrets and runtime configuration out of this file.
"""

from dataclasses import dataclass
from pydantic import BaseModel
from typing import Optional


@dataclass
class Book:
    """Simple dataclass used by local tooling or seed scripts.

    Attributes:
        id: integer book identifier used by seed data
        title: the book title
        author: the book author
    """
    id: int
    title: str
    author: str


class ConfirmRequest(BaseModel):
    """Minimal model used when confirming a hold via the HTTP API.

    This mirrors the ConfirmRequest used in the main FastAPI app. It only
    contains the subset of fields needed by the API endpoint that live in
    this module for convenience in tests or other callers.
    """
    holdId: str
    isOpenToJoin: bool = False

    class Config:
        # Allow population by field name and keep models simple
        arbitrary_types_allowed = True
