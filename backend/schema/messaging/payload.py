from typing import Any, Dict, Literal, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from ..blocks import (
    CardSchema,
    UserSchema,
    CardPreferenceSchema,
    StoreSchema,
)


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
    store: Optional[StoreSchema] = Field(
        None, description="The slug of the store to check."
    )
    card_data: Optional[CardPreferenceSchema] = Field(
        None,
        description="The card details, including name and specifications."
    )


class AvailabilityResultPayload(Payload):
    """
    Defines the payload for a message published by a worker to the
    'worker-results' Redis channel after completing a scraping task.
    """
    model_config = ConfigDict(from_attributes=True)
    card: CardPreferenceSchema = Field(
        ..., description="The card being checked."
    )
    store: StoreSchema = Field(
        ..., description="The store being checked."
    )

    items: List[Dict[str, Any]] = Field(
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
        ..., description="The raw text of the card list to be parsed."
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
        ..., min_length=3,
        description="The search term for card name autocomplete."
    )


class CardListPayload(Payload):
    """
    Payload for a list of cards.
    """

    cards: list[CardPreferenceSchema] = Field(...,
                                              description="A list of cards.")


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


class LoginUserPayload(Payload):
    """
    Payload for the result of fetching user data.
    """

    user: UserSchema = Field(..., description="The user data.")
    password: str = Field(..., description="The user's password.")


class GetCardsPayload(Payload):
    """
    Payload for getting a card
    """
    user: UserSchema = Field(..., description="The User")


class UpdateStoresPayload(Payload):
    """
    Payload for updating a user's preferred stores.
    """

    stores: list[StoreSchema] = Field(...,
                                      description="A list of store slugs.")
    user: UserSchema = Field(..., description="The user data.")
