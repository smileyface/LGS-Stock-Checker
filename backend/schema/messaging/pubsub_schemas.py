from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CardSpecsSchema(BaseModel):
    """
    Represents the specific printing details of a card.
    All fields are optional, allowing for partial or wildcard tracking.
    This schema is reused from socket_schemas.py for consistency.
    """

    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    finish: Optional[str] = None


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

    username: str = Field(
        ..., description="The user the results belong to."
        )
    store_slug: str = Field(
        ..., description="The slug of the store that was checked."
        )
    card: str = Field(
        ..., description="The name of the card that was checked."
        )
    items: List[Dict[str, Any]] = Field(
        ..., description="A list of available items found at the store."
    )
