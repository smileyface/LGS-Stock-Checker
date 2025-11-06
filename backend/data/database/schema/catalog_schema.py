"""
Pydantic schemas for catalog-related data, such as finishes and card printings.
These are used for data validation and serialization.
"""

from pydantic import BaseModel, ConfigDict
from typing import List


class FinishSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class CardPrintingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    card_name: str
    set_code: str
    collector_number: int
    available_finishes: List[FinishSchema]
