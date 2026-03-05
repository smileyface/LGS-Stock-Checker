from typing import List
from pydantic import (ConfigDict,
                      Field,
                      computed_field)

from ..blocks import (
    CardSchema,
    CardSpecificationSchema,
)

from .base_schema import DatabaseSchema


class CardPrintingSchema(DatabaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Database ID.")

    # The ORM has 'card_name' (string)
    card_name: str = Field(..., description="Name of the card.")
    amount: int = Field(..., description="Quantity.")

    # We use the schema from blocks.py that handles the
    #  Union[SetSchema, str] logic
    specifications: List[CardSpecificationSchema] = Field(default_factory=list)

    # COMPATIBILITY LAYER:
    # The database model likely doesn't have a populated 'card' relationship
    # (or it's lazy loaded and currently None).
    # However, the frontend or API contract
    # might expect a nested 'card' object.
    # We compute this field dynamically from 'card_name' to
    # ensure it's always present and valid.
    @computed_field
    def card(self) -> CardSchema:
        return CardSchema(name=self.card_name)
