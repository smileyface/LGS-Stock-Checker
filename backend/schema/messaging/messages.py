from typing import Union
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from .payload import (
    Payload,
    AvailabilityRequestPayload,
    AvailabilityResultPayload,
    GetPrintingsRequestPayload,
    UpdateCardRequestPayload,
)


# --- Messaging Base Definitions ---
class PubSubMessage(BaseModel):
    """Base class for pub-sub messages."""
    name: str
    channel: str

    def __init__(self,
                 **data):
        super().__init__(**data)
        self.payload = Payload()


class APIMessage(BaseModel):
    """Base class for all API messages."""
    name: str

    def __init__(self,
                 name: str,
                 **data):
        super().__init__(**data)
        self.name = name
        self.payload = Payload()
# --- End Messaging Base Definitions ---


# --- Pub-Sub Message Definitions ---
class AvailabilityRequestCommand(PubSubMessage):
    """A specific command to request a single availability check."""
    payload: AvailabilityRequestPayload

    def __init__(self,
                 payload: AvailabilityRequestPayload,
                 **data):
        super().__init__(**data)
        self.name = "availability_request"
        self.channel = "scheduler-requests"
        self.payload = payload


class QueueAllAvailabilityChecksCommand(PubSubMessage):
    """A specific command to queue checks for all of a user's cards."""

    def __init__(self,
                 **data):
        super().__init__(**data)
        self.name = "queue_all_availability_checks"
        self.channel = "scheduler-requests"


class AvailabilityResultMessage(PubSubMessage):
    """
    Defines the structure for a message published by a worker to the
    'worker-results' Redis channel after completing a scraping task.
    """
    payload: AvailabilityResultPayload

    def __init__(self,
                 payload: AvailabilityResultPayload,
                 **data):
        super().__init__(**data)
        self.name = "availability_result"
        self.channel = "worker-results"
        self.payload = payload
# --- End Pub-Sub Message Definitions ---


# --- API Message Definitions ---
class GetCardPrintingsMessage(APIMessage):
    """
    Message to request card printings from the API.
    """
    payload: GetPrintingsRequestPayload

    def __init__(self,
                 payload: GetPrintingsRequestPayload,
                 **data):
        super().__init__("get_card_printings", **data)
        self.payload = payload


class ParseCardListMessage(APIMessage):
    """
    Message to parse a card list from the API.
    """
    payload: dict

    def __init__(self,
                 payload: dict,
                 **data):
        super().__init__("parse_card_list", **data)
        self.payload = payload


class AddCardMessage(APIMessage):
    """
    Message to add a card to the API.
    """
    payload: UpdateCardRequestPayload

    def __init__(self,
                 payload: UpdateCardRequestPayload,
                 **data):
        super().__init__("add_card", **data)
        self.payload = payload


class DeleteCardMessage(APIMessage):
    """
    Message to delete a card from the API.
    """
    payload: UpdateCardRequestPayload

    def __init__(self,
                 payload: UpdateCardRequestPayload,
                 **data):
        super().__init__("delete_card", **data)
        self.payload = payload


class UpdateCardMessage(APIMessage):
    """
    Message to update a card in the API.
    """
    payload: UpdateCardRequestPayload

    def __init__(self,
                 payload: UpdateCardRequestPayload,
                 **data):
        super().__init__("update_card", **data)
        self.payload = payload


class SearchCardNamesMessage(APIMessage):
    """
    Message to search for card names in the API.
    """
    payload: dict

    def __init__(self,
                 payload: dict,
                 **data):
        super().__init__("search_card_names", **data)
        self.payload = payload


class UpdateStoreMessage(APIMessage):
    """
    Message to update a user's preferred stores in the API.
    """
    stores: list[str]

    def __init__(self,
                 stores: list[str],
                 **data):
        super().__init__("update_stores", **data)
        self.stores = stores
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
