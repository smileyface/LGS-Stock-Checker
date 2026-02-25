from typing import List, Optional
from pydantic import Field, ConfigDict, computed_field


from .store_schema import StoreSchema
from .base_schema import DatabaseSchema

from ..blocks import (
    CardSchema,
    CardSpecificationSchema,
)


class UserTrackedCardSchema(DatabaseSchema):
    model_config = ConfigDict(
        from_attributes=True
    )

    # The ORM model has 'card_name', not a populated 'card' relationship by default
    card_name: str = Field(..., description="The name of the card.")

    amount: int = Field(
        1,
        ge=1,
        description="The quantity of the card the user wants to track."
    )
    specifications: List[CardSpecificationSchema] = Field(
        [], description="List of specific versions of the card."
    )

    # Compute the nested 'card' object dynamically to satisfy frontend expectations
    # without relying on the ORM relationship being loaded.
    @computed_field
    def card(self) -> CardSchema:
        return CardSchema(name=self.card_name)


class UserTrackedCardListSchema(DatabaseSchema):
    tracked_cards: List[UserTrackedCardSchema] = Field(
        ..., description="List of cards tracked by the user."
    )


class UserTrackedCardUpdateSchema(DatabaseSchema):
    """Schema for updating a user's tracked card, allowing partial updates."""
    amount: Optional[int] = Field(
        None,
        ge=1,
        description="The quantity of the card the user wants to track."
    )
    specifications: Optional[List[CardSpecificationSchema]] = Field(
        None, description="List of specific versions of the card."
    )


# Schema for User data including sensitive password_hash,
# used internally by backend.
class UserDBSchema(DatabaseSchema):
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
    cards: List[UserTrackedCardSchema] = Field(
        [], description="List of cards tracked by the user."
    )


class UserPublicSchema(DatabaseSchema):
    model_config = ConfigDict(
        from_attributes=True
    )

    username: str
    selected_stores: List[StoreSchema] = Field(
        [], description="List of stores selected by the user."
    )
    cards: List[UserTrackedCardSchema] = Field(
        [], description="List of cards tracked by the user."
    )
