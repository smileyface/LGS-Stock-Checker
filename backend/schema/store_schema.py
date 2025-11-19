from typing import List
from pydantic import BaseModel, ConfigDict, Field


class StoreSchema(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    id: int
    name: str
    slug: str
    homepage: str
    search_url: str
    fetch_strategy: str

    model_config = ConfigDict(from_attributes=True)


class UpdateStoreSchema(BaseModel):
    """Schema for validating the payload of the 'store_update' event."""
    """
    Validates the payload for the 'update_stores' event.
    """

    store: str
    stores: List[str] = Field(
        ..., description="A list of store slugs the user wants to track."
    )
