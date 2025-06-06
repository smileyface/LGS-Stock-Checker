from typing import List
from pydantic import BaseModel  # pip install pydantic

from data.schema import CardSpecificationSchema
from data.schema.store_schema import StoreSchema


class UserSchema(BaseModel):
    username: str
    selected_stores: List[StoreSchema] = []  # List of StoreSchema DTOs
    # Add other user fields as needed

    class Config:
        from_attributes = True # <--- THIS IS CRUCIAL FOR ORM CONVERSION


class UserTrackedCardSchema(BaseModel):
    card_name: str
    amount: int
    specifications: List[CardSpecificationSchema] = []
