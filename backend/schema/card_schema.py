from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict


class FinishSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: Literal["normal", "foil", "etched"]


class CardSchema(BaseModel):
    id: int
    name: str


class CardSpecificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    set_code: Optional[str] = Field(
        None, description="The set code (e.g., 'ONE'). Null if any set."
    )
    collector_number: Optional[str] = Field(
        None, description="The collector number. Null if any."
    )
    finish: Optional[FinishSchema] = Field(
        None,
        description="The card's finish ('normal', 'foil', 'etched'). "
        "Defaults to None.",
    )


class CardPrintingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    card_name: str
    specification: CardSpecificationSchema
    available_finishes: List[FinishSchema]
