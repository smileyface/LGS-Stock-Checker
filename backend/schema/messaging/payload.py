from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field
from ..blocks import (CardSchema,
                      CardSpecificationSchema,
                      UserSchema,
                      CardPreferenceSchema)


class Payload(BaseModel):
    """Base class for all messaging payloads."""
    pass


class AvailabilityRequestPayload(BaseModel):
    """
    Defines the payload for a command sent to the Scheduler to request
    a new availability check task.
    """

    user: UserSchema = Field(
        ..., description="The user requesting the availability check."
        )
    store_slug: Optional[str] = Field(
        ..., description="The slug of the store to check."
        )
    card_data: Optional[CardSpecificationSchema] = Field(
        ..., description="The card details, including name and specifications."
    )


class AvailabilityResultPayload(BaseModel):
    """
    Defines the payload for a message published by a worker to the
    'worker-results' Redis channel after completing a scraping task.
    """

    respondent: AvailabilityRequestPayload = Field(
        ..., description="The card responding to."
    )

    items: Dict[str, Any] = Field(
        ..., description="A list of available items found at the store."
    )


class GetPrintingsRequestPayload(BaseModel):
    """
    Validates the payload for the 'get_card_printings' event.
    """
    card_name: CardSchema = Field(..., min_length=1)


class ParseCardListRequestPayload(BaseModel):
    """Schema for validating the payload of the 'parse_card_list' event."""

    raw_list: str = Field(
        ...,
        description="The raw text of the card list to be parsed."
    )


class UpdateCardRequestPayload(BaseModel):
    """
    Validates the payload for the 'update_card' event.
    """
    command: Literal["add", "delete", "update"]
    update_data: CardPreferenceSchema


class SearchCardNamesSchema(BaseModel):
    """
    Validates the payload for the 'search_card_names' event.
    """

    query: str = Field(
        ...,
        min_length=3,
        description="The search term for card name autocomplete."
    )
