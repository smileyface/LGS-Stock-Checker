from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ParseCardListSchema(BaseModel):
    """Schema for validating the payload of the 'parse_card_list' event."""
    raw_list: str


class AddCardSchema(BaseModel):
    """Schema for validating the payload of the 'add_card' event."""
    card: str
    amount: int = Field(ge=1)
    card_specs: List[Dict[str, Any]] = []


class DeleteCardSchema(BaseModel):
    """Schema for validating the payload of the 'delete_card' event."""
    card: str


class UpdateCardSchema(BaseModel):
    """Schema for validating the payload of the 'update_card' event."""
    card: str
    update_data: Dict[str, Any]