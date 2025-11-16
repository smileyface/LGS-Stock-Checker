from typing import List
from pydantic import BaseModel, Field, ConfigDict

from data.database.schema import CardSpecificationSchema
from data.database.schema.store_schema import StoreSchema


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

    # Add other internal user fields as needed


class UserPublicSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )  # <--- THIS IS CRUCIAL FOR ORM CONVERSION

    username: str
    # Assuming selected_stores is a relationship that returns ORM Store objects
    selected_stores: List[StoreSchema] = Field(
        [], description="List of stores selected by the user."
    )

    # Add other user fields as needed


class UserTrackedCardSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    card_name: str = Field(
        ..., description="The name of the card being tracked."
    )
    amount: int = Field(
        1,
        ge=1,
        description="The quantity of the card the user wants to track."
    )
    specifications: List[CardSpecificationSchema] = Field(
        [], description="List of specific versions of the card."
    )
