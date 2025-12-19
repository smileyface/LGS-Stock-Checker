from typing import Union, Literal, TypeVar, Generic, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Annotated
from .payload import (
    Payload,
    AvailabilityRequestPayload,
    AvailabilityResultPayload,
    GetPrintingsRequestPayload,
    UpdateCardRequestPayload,
    CatalogPrintingsChunkResultPayload,
    CatalogFinishesChunkResultPayload,
    CatalogCardNamesResultPayload,
    CatalogSetDataResultPayload,
)


# --- Messaging Base Definitions ---
T = TypeVar("T", bound=Payload)


class PubSubMessage(BaseModel, Generic[T]):
    """Base class for pub-sub messages."""
    channel: ClassVar[str]
    payload: T


class APIMessage(BaseModel):
    """Base class for all API messages."""
    pass
# --- End Messaging Base Definitions ---


# --- Pub-Sub Message Definitions ---
class AvailabilityRequestCommand(PubSubMessage[AvailabilityRequestPayload]):
    """A specific command to request a single availability check."""
    model_config = ConfigDict(from_attributes=True)
    name: Literal["availability_request"] = "availability_request"
    channel: ClassVar[str] = "scheduler-requests"
    payload: AvailabilityRequestPayload


class QueueAllAvailabilityChecksCommand(PubSubMessage[Payload]):
    """A specific command to queue checks for all of a user's cards."""
    name: Literal["queue_all_availability_checks"] = "queue_all_availability_checks"
    channel: ClassVar[str] = "scheduler-requests"


class AvailabilityResultMessage(PubSubMessage[AvailabilityResultPayload]):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a scraping task.
    """
    name: Literal["availability_result"] = "availability_result"
    channel: ClassVar[str] = "worker-results"
    payload: AvailabilityResultPayload


class CatalogCardNamesResultMessage(PubSubMessage[CatalogCardNamesResultPayload]):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a catalog card names task.
    """
    name: Literal["catalog_card_names_result"] = "catalog_card_names_result"
    channel: ClassVar[str] = "worker-results"
    payload: CatalogCardNamesResultPayload


class CatalogSetDataResultMessage(PubSubMessage[CatalogSetDataResultPayload]):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a catalog set data task.
    """
    name: Literal["catalog_set_data_result"] = "catalog_set_data_result"
    channel: ClassVar[str] = "worker-results"
    payload: CatalogSetDataResultPayload


class CatalogPrintingsChunkResultMessage(PubSubMessage[
                                        CatalogPrintingsChunkResultPayload]):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a catalog printings chunk task.
    """
    name: Literal["catalog_printings_chunk_result"] = "catalog_printings_chunk_result"
    channel: ClassVar[str] = "worker-results"
    payload: CatalogPrintingsChunkResultPayload


class CatalogFinishesChunkResultMessage(PubSubMessage[
                                      CatalogFinishesChunkResultPayload]):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a catalog finishes chunk task.
    """
    name: Literal["catalog_finishes_chunk_result"] = "catalog_finishes_chunk_result"
    channel: ClassVar[str] = "worker-results"
    payload: CatalogFinishesChunkResultPayload
# --- End Pub-Sub Message Definitions ---


# --- API Message Definitions ---
class GetCardPrintingsMessage(APIMessage):
    """
    Message to request card printings from the API.
    """
    name: Literal["get_card_printings"] = "get_card_printings"
    payload: GetPrintingsRequestPayload


class ParseCardListMessage(APIMessage):
    """
    Message to parse a card list from the API.
    """
    name: Literal["parse_card_list"] = "parse_card_list"
    payload: dict


class UpdateCardRequest(APIMessage):
    """
    A unified update message to handle add, delete, and update requests.
    """
    # This message uses dynamic names (e.g. "add_card_CardName"), so we keep it as str.
    name: str
    payload: UpdateCardRequestPayload


class AddCardMessage(APIMessage):
    """
    Message to add a card to the API.
    """
    name: Literal["add_card"] = "add_card"
    payload: UpdateCardRequestPayload


class DeleteCardMessage(APIMessage):
    """
    Message to delete a card from the API.
    """
    name: Literal["delete_card"] = "delete_card"
    payload: UpdateCardRequestPayload


class UpdateCardMessage(APIMessage):
    """
    Message to update a card in the API.
    """
    name: Literal["update_card"] = "update_card"
    payload: UpdateCardRequestPayload


class SearchCardNamesMessage(APIMessage):
    """
    Message to search for card names in the API.
    """
    name: Literal["search_card_names"] = "search_card_names"
    payload: dict


class UpdateStoreMessage(APIMessage):
    """
    Message to update a user's preferred stores in the API.
    """
    name: Literal["update_stores"] = "update_stores"
    stores: list[str]
# --- End API Message Definitions ---


# --- Discriminated Union ---
Messages = Annotated[
    # pub-sub message types
    Union[AvailabilityRequestCommand,
          QueueAllAvailabilityChecksCommand,
          AvailabilityResultMessage],
    Field(discriminator="name"),
]
# --- End Discriminated Union ---
