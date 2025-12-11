from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from .card_schema import CardSpecificationSchema
from .store_schema import StoreSchema

from ..blocks import (
    CardSchema,
)


# Schema for User data including sensitive password_hash,
# used internally by backend.
class UserDBSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )  # Crucial for converting ORM User objects

    username: str = Field(..., description="The user's unique username.")
    password_hash: str = Field(
        ..., description="The hashed password for authentication."
    )
    selected_stores: List[StoreSchema] = Field(
        [], description="List of stores selected by the user."
    )


class UserPublicSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    username: str
    selected_stores: List[StoreSchema] = Field(
        [], description="List of stores selected by the user."
    )


class UserTrackedCardSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
        )

    card: CardSchema = Field(..., description="The card being tracked.")

    amount: int = Field(
        1,
        ge=1,
        description="The quantity of the card the user wants to track."
    )
    specifications: List[CardSpecificationSchema] = Field(
        [], description="List of specific versions of the card."
    )


class UserTrackedCardListSchema(BaseModel):
    tracked_cards: List[UserTrackedCardSchema] = Field(
        ..., description="List of cards tracked by the user."
    )


class UserTrackedCardUpdateSchema(BaseModel):
    """Schema for updating a user's tracked card, allowing partial updates."""
    amount: Optional[int] = Field(
        None,
        ge=1,
        description="The quantity of the card the user wants to track."
    )
    specifications: Optional[List[CardSpecificationSchema]] = Field(
        None, description="List of specific versions of the card."
    )
