from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing_extensions import Self


class FinishSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Literal["non-foil", "foil", "etched"]


class CardSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(...,
                      description="The name of the card.",
                      min_length=1)


class SetSchema(BaseModel):
    """
    Schema for a set, including its code and name.
    At least one of 'code' or 'name' must be provided.
    """

    model_config = ConfigDict(from_attributes=True)
    code: Optional[str] = None
    name: Optional[str] = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> Self:
        """Ensures that at least one of 'code' or 'name' is provided."""
        if not self.code and not self.name:
            raise ValueError("At least one of 'code' \
                             or 'name' must be provided.")
        return self
