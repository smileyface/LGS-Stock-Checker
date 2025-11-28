from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from ..blocks import (
    FinishSchema,
    CardSchema,
    SetSchema,
)


class CardSpecificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    set_code: Optional[SetSchema] = Field(
        None, description="The set code (e.g., 'ONE'). Null if any set."
    )
    collector_number: Optional[str] = Field(
        None, description="The collector number. Null if any."
    )
    finish: Optional[FinishSchema] = Field(
        None,
        description="The card's finish ('non-foil', 'foil', 'etched'). "
        "Defaults to None.",
    )


class CardPrintingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    card_name: CardSchema
    specification: Optional[CardSpecificationSchema]
    available_finishes: Optional[FinishSchema]
