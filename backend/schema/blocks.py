from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing_extensions import Self


class FinishSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Literal["non-foil", "foil", "etched"]

    def __str__(self) -> str:
        return self.name


class CardSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(...,
                      description="The name of the card.",
                      min_length=1)

    def __str__(self) -> str:
        return self.name


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

    def __str__(self) -> str:
        if self.code:
            return self.code
        elif self.name:
            return self.name
        else:
            return "Unknown Set"


class CardSpecificationSchema(BaseModel):
    """
    Represents the specific printing details of a card.
    All fields are optional, allowing for partial or wildcard tracking.
    """

    set_code: Optional[SetSchema] = None
    collector_number: Optional[str] = None
    finish: Optional[FinishSchema] = None

    def get_key(self) -> tuple[Optional[str],
                               Optional[str],
                               Optional[str]]:
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


class UserSchema(BaseModel):
    """
    Schema for a user, including their username.
    """

    model_config = ConfigDict(from_attributes=True)
    username: str = Field(...,
                          description="The username of the user.",
                          min_length=1)

    def __str__(self) -> str:
        return self.username


class CardPreferenceSchema(BaseModel):
    """
    Schema representing a user's preference for a specific card,
    including optional specifications.
    """

    card: CardSchema = Field(..., description="The card being tracked.")
    amount: Optional[int] = Field(...,
                                  gt=0,
                                  description="The quantity of the card to track.")
    card_specs: Optional[CardSpecificationSchema] = Field(
        None, description="Optional printing specifications for the card."
    )
