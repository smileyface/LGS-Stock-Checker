from typing import List
from pydantic import BaseModel, Field  # pip install pydantic

from data.schema import CardSpecificationSchema
from data.schema.store_schema import StoreSchema


class UserSchema(BaseModel):
    username: str
    # Assuming selected_stores is a relationship that returns ORM Store objects
    selected_stores: List[StoreSchema] = Field([], description="List of stores selected by the user.")
    # Add other user fields as needed

    class Config:
        from_attributes = True # <--- THIS IS CRUCIAL FOR ORM CONVERSION


class UserTrackedCardSchema(BaseModel):
    card_name: str = Field(..., description="The name of the card being tracked.")
    amount: int = Field(1, ge=1, description="The quantity of the card the user wants to track.")
    specifications: List[CardSpecificationSchema] = Field([], description="List of specific versions of the card.")

    class Config:
        from_attributes = True # <--- Needs to be here too
