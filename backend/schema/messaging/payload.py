from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict
from ..blocks import (CardSchema,
                      CardSpecificationSchema,
                      UserSchema,
                      CardPreferenceSchema)


class Payload(BaseModel):
    """Base class for all messaging payloads."""
    pass


class AvailabilityRequestPayload(Payload):
    """
    Defines the payload for a command sent to the Scheduler to request
    a new availability check task.
    """
    model_config = ConfigDict(from_attributes=True)
    user: UserSchema = Field(
        ..., description="The user requesting the availability check."
        )
    store_slug: Optional[str] = Field(
        ..., description="The slug of the store to check."
        )
    card_data: Optional[CardSpecificationSchema] = Field(
        ..., description="The card details, including name and specifications."
    )


class AvailabilityResultPayload(Payload):
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


class GetPrintingsRequestPayload(Payload):
    """
    Validates the payload for the 'get_card_printings' event.
    """
    card: CardSchema = Field(...)


class ParseCardListRequestPayload(Payload):
    """Schema for validating the payload of the 'parse_card_list' event."""

    raw_list: str = Field(
        ...,
        description="The raw text of the card list to be parsed."
    )


class UpdateCardRequestPayload(Payload):
    """
    Validates the payload for the 'update_card' event.
    """
    command: Literal["add", "delete", "update"]
    update_data: CardPreferenceSchema


class SearchCardNamesSchema(Payload):
    """
    Validates the payload for the 'search_card_names' event.
    """

    query: str = Field(
        ...,
        min_length=3,
        description="The search term for card name autocomplete."
    )


class CatalogCardChunkPayload(Payload):
    """
    Payload for a chunk of card data to be processed.
    """
    printings: list[CardSchema] = Field(...,
                                        description="A list of "
                                        "card printings.")


class CatalogFinishesChunkPayload(Payload):
    """
    Payload for a chunk of finishes data to be processed.
    """
    finishes: list[str] = Field(..., description="A list of unique finishes.")


class CatalogPrintingsChunkPayload(Payload):
    """
    Payload for a chunk of printings data to be processed.
    """
    pass


class CatalogCardNamesResultPayload(Payload):
    """
    Payload for the result of fetching catalog card names.
    """
    names: list[str] = Field(..., description="A list of card names.")


class CatalogSetDataResultPayload(Payload):
    """
    Payload for the result of fetching catalog set data.
    """
    sets: list[dict] = Field(..., description="A list of set data.")


class CatalogPrintingsChunkResultPayload(Payload):
    """
    Payload for the result of processing card printings in chunks.
    """
    printings: list[dict] = Field(..., description="A list of card printings.")


class CatalogFinishesChunkResultPayload(Payload):
    """
    Payload for the result of processing finishes in chunks.
    """
    finishes: list[str] = Field(..., description="A list of finishes.")
