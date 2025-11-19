from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GetPrintingsSchema(BaseModel):
    """
    Validates the payload for the 'get_card_printings' event.
    """

    card_name: str = Field(..., min_length=1)


class CardSpecsSchema(BaseModel):
    """
    Represents the specific printing details of a card.
    All fields are optional, allowing for partial or wildcard tracking.
    """

    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    finish: Optional[str] = None


class ParseCardListSchema(BaseModel):
    """Schema for validating the payload of the 'parse_card_list' event."""

    raw_list: str


class AddCardSchema(BaseModel):
    """
    Validates the payload for the 'add_card' event.
    """

    card: str = Field(
        ..., min_length=1, description="The name of the card to add."
        )
    amount: int = Field(
        ..., gt=0, description="The quantity of the card to track."
        )
    card_specs: Optional[CardSpecsSchema] = Field(
        None, description="Optional printing specifications for the card."
    )


class DeleteCardSchema(BaseModel):
    """Schema for validating the payload of the 'delete_card' event."""
    """
    Validates the payload for the 'delete_card' event.
    """

    card: str


class UpdateCardSchema(BaseModel):
    """Schema for validating the payload of the 'update_card' event."""
    """
    Validates the payload for the 'update_card' event.
    """

    card: str
    update_data: Dict[str, Any]


class SearchCardNamesSchema(BaseModel):
    """
    Validates the payload for the 'search_card_names' event.
    """

    query: str = Field(
        ...,
        min_length=3,
        description="The search term for card name autocomplete."
    )


class CardSpecsSchema(BaseModel):
    """
    Represents the specific printing details of a card.
    All fields are optional, allowing for partial or wildcard tracking.
    """

    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    finish: Optional[str] = None
