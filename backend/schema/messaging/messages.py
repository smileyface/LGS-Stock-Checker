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
    UpdateStoresPayload,
    LoginUserPayload,
    CardListPayload,
)


# --- Messaging Base Definitions ---
T = TypeVar("T", bound=Payload)


class PubSubMessage(BaseModel, Generic[T]):
    """Base class for pub-sub messages."""

    channel: ClassVar[str]
    name: ClassVar[str]
    payload: T


class APIMessage(BaseModel):
    """Base class for all API messages."""

    pass


# --- End Messaging Base Definitions ---


# --- Pub-Sub Message Definitions ---
class AvailabilityRequestCommand(PubSubMessage[AvailabilityRequestPayload]):
    """A specific command to request a single availability check."""

    model_config = ConfigDict(from_attributes=True)
    name: ClassVar[str] = "availability_request"
    channel: ClassVar[str] = "scheduler-requests"
    payload: AvailabilityRequestPayload


class QueueAllAvailabilityChecksCommand(PubSubMessage[Payload]):
    """A specific command to queue checks for all of a user's cards."""

    name: ClassVar[str] = "queue_all_availability_checks"
    channel: ClassVar[str] = "scheduler-requests"


class AvailabilityResultMessage(PubSubMessage[AvailabilityResultPayload]):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a scraping task.
    """

    name: ClassVar[str] = "availability_result"
    channel: ClassVar[str] = "worker-results"
    payload: AvailabilityResultPayload


class CatalogCardNamesResultMessage(
        PubSubMessage[CatalogCardNamesResultPayload]):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a catalog card names task.
    """

    name: ClassVar[str] = "catalog_card_names_result"
    channel: ClassVar[str] = "worker-results"
    payload: CatalogCardNamesResultPayload


class CatalogSetDataResultMessage(PubSubMessage[CatalogSetDataResultPayload]):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a catalog set data task.
    """

    name: ClassVar[str] = "catalog_set_data_result"
    channel: ClassVar[str] = "worker-results"
    payload: CatalogSetDataResultPayload


class CatalogPrintingsChunkResultMessage(
    PubSubMessage[CatalogPrintingsChunkResultPayload]
):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a catalog printings
    chunk task.
    """

    name: ClassVar[str] = "catalog_printings_chunk_result"
    channel: ClassVar[str] = "worker-results"
    payload: CatalogPrintingsChunkResultPayload


class CatalogFinishesChunkResultMessage(
    PubSubMessage[CatalogFinishesChunkResultPayload]
):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a catalog
    finishes chunk task.
    """

    name: ClassVar[str] = "catalog_finishes_chunk_result"
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

    # This message uses dynamic names
    # (e.g. "add_card_CardName"), so we keep it as str.
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
    stores: UpdateStoresPayload


class LoginUserMessage(APIMessage):
    """
    Message to retrieve the currently authenticated user's information.
    """

    name: Literal["login_user_me"] = "login_user_me"
    payload: LoginUserPayload


# --- End API Message Definitions ---


# --- Begin API Response Message Definitions ---
class CardsDataMessage(APIMessage):
    """
    Message to send a user's tracked cards to the frontend.
    """

    name: Literal["cards_data"] = "cards_data"
    payload: CardListPayload


class CardPrintingsDataMessage(APIMessage):
    """
    Message to send card printings data to the frontend.
    """

    name: Literal["card_printings_data"] = "card_printings_data"
    payload: dict


class CardAvailabilityDataMessage(APIMessage):
    """
    Message to send card availability data to the frontend.
    """

    name: Literal["card_availability_data"] = "card_availability_data"
    payload: dict


class CardNameSearchResultsMessage(APIMessage):
    """
    Message to send card name search results to the frontend.
    """

    name: Literal["card_name_search_results"] = "card_name_search_results"
    payload: dict


class UserStoresDataMessage(APIMessage):
    """
    Message to send a user's preferred stores to the frontend.
    """

    name: Literal["user_stores_data"] = "user_stores_data"
    payload: dict


class StockDataMessage(APIMessage):
    """
    Message to send aggregated stock data for a card to the frontend.
    """

    name: Literal["stock_data"] = "stock_data"
    payload: dict


class ErrorMessage(APIMessage):
    """
    Message to send error information to the frontend.
    """

    name: Literal["error"] = "error"
    payload: dict


# --- End API Response Message Definitions ---)


# --- Discriminated Union ---
PubSubMessages = Annotated[
    # pub-sub message types
    Union[
        AvailabilityRequestCommand,
        QueueAllAvailabilityChecksCommand,
        AvailabilityResultMessage,
        CatalogCardNamesResultMessage,
        CatalogSetDataResultMessage,
        CatalogPrintingsChunkResultMessage,
        CatalogFinishesChunkResultMessage,
    ],
    Field(discriminator="name"),
]

APIMessages = Annotated[
    Union[
        GetCardPrintingsMessage,
        ParseCardListMessage,
        UpdateCardRequest,
        AddCardMessage,
        DeleteCardMessage,
        UpdateCardMessage,
        SearchCardNamesMessage,
        UpdateStoreMessage,
        LoginUserMessage,
    ],
    Field(discriminator="name"),
]

APIMessageResponses = Annotated[
    Union[
        CardsDataMessage,
        CardPrintingsDataMessage,
        CardAvailabilityDataMessage,
        CardNameSearchResultsMessage,
        UserStoresDataMessage,
        StockDataMessage,
        ErrorMessage,
    ],
    Field(discriminator="name"),
]
# --- End Discriminated Union ---
