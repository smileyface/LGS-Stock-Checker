from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CardSpecsSchema(BaseModel):
    """
    Represents the specific printing details of a card.
    All fields are optional, allowing for partial or wildcard tracking.
    """

    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    finish: Optional[Literal["non-foil", "foil", "etched"]] = None


class AvailabilityRequestPayload(BaseModel):
    """
    Defines the payload for a command sent to the Scheduler to request
    a new availability check task.
    """

    username: str = Field(
        ..., description="The user who initiated the request."
        )
    store_slug: str = Field(
        ..., description="The slug of the store to check."
        )
    card_data: Dict[str, Any] = Field(
        ..., description="The card details, including name and specifications."
    )


class SchedulerCommand(BaseModel):
    """
    Defines the overall structure for a message published to the
    'scheduler-requests' Redis channel.
    """

    command: Literal["availability_request"]
    payload: AvailabilityRequestPayload


class AvailabilityResult(BaseModel):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a scraping task.
    """

    respondent: AvailabilityRequestPayload = Field(
        ..., description="The card responding to."
    )

    items: List[Dict[str, Any]] = Field(
        ..., description="A list of available items found at the store."
    )


class GetPrintingsSchema(BaseModel):
    """
    Validates the payload for the 'get_card_printings' event.
    """

    card_name: str = Field(..., min_length=1)


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
    card: str = Field(..., min_length=1)


class UpdateCardSchema(BaseModel):
    """Schema for validating the payload of the 'update_card' event."""
    """
    Validates the payload for the 'update_card' event.
    """

    card: str = Field(..., min_length=1)
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


class GetCardPrintings(BaseModel):
    card_name: str = Field(..., min_length=1)
