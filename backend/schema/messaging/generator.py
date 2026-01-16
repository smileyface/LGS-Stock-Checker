from .messages import (
    AvailabilityRequestCommand,
    AvailabilityResultMessage,
)

from .payload import (
    AvailabilityRequestPayload,
    AvailabilityResultPayload,
)

from ..blocks import UserSchema, CardPreferenceSchema, StoreSchema


def GenerateAvailabilityRequestCommand(
    username, store, card_data
) -> AvailabilityRequestCommand:
    payload = AvailabilityRequestPayload(
        user=UserSchema(username=username),
        store=StoreSchema.model_validate(store),
        card_data=CardPreferenceSchema.model_validate(card_data),
    )
    return AvailabilityRequestCommand(payload=payload)


def GenerateAvailabilityResult(
    card: dict, store: dict, items: list[dict]
) -> AvailabilityResultMessage:
    payload = AvailabilityResultPayload(
        card=CardPreferenceSchema.model_validate(card),
        store=StoreSchema.model_validate(store),
        items=items,
    )
    return AvailabilityResultMessage(payload=payload)
