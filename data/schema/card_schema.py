from typing import Optional

from pydantic import BaseModel, Field


class CardSpecificationSchema(BaseModel):
    set_code: Optional[str] = Field(None, description="The set code (e.g., 'ONE'). Null if any set.")
    collector_number: Optional[str] = Field(None, description="The collector number. Null if any.")
    finish: Optional[str] = Field("normal", description="The card's finish ('normal', 'foil', 'etched'). Defaults to 'normal'.")

    class Config:
        from_attributes = True
