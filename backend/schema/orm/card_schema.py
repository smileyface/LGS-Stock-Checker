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

    def get_key(self) -> tuple[Optional[str], Optional[str], Optional[str]]:
        return (
            self.set_code.code if self.set_code else None,
            self.collector_number,
            self.finish.name if self.finish else None,
        )

    def to_dict(self) -> dict:
        return {
            "set_code": self.set_code.code if self.set_code else None,
            "collector_number": self.collector_number,
            "finish": self.finish.name if self.finish else None,
        }


class CardPrintingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    card_name: CardSchema
    specification: Optional[CardSpecificationSchema]
    available_finishes: Optional[FinishSchema]
