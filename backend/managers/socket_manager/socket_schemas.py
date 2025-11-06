from typing import Any, Dict, List

from pydantic import BaseModel, Field

class GetPrintingsSchema(BaseModel):
    card_name: str

class ParseCardListSchema(BaseModel):
    """Schema for validating the payload of the 'parse_card_list' event."""
    raw_list: str


class AddCardSchema(BaseModel):
    card: str
    amount: int = Field(ge=1)
    card_specs: Dict[str, Any] = {}


class DeleteCardSchema(BaseModel):
    """Schema for validating the payload of the 'delete_card' event."""
    card: str


class UpdateCardSchema(BaseModel):
    """Schema for validating the payload of the 'update_card' event."""
    card: str
    update_data: Dict[str, Any]


class UpdateStoreSchema(BaseModel):
    """Schema for validating the payload of the 'store_update' event."""
    store: str
