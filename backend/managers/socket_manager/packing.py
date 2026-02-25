from schema.blocks import (CardSchema,
                           CardSpecificationSchema,
                           SetSchema,
                           FinishSchema,
                           )
from data.database.models.orm_models import (UserTrackedCards,
                                             CardSpecification)


def pack_specifications(specification: CardSpecification) -> dict:
    """
    Packs a list of specification dictionaries into a standardized format for messaging.

    Args:
        specifications (list[dict]): A list of dictionaries, where each
                                     dictionary represents a card specification.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary is a
                    CardSpecificationSchema model_dump.
    """
    spec = {}
    if specification.set_code is not None:
        spec["set_code"] = specification.set_code
    if specification.finish is not None:
        spec["finish"] = specification.finish.to_dict()
    if specification.collector_number is not None:
        spec["collector_number"] = specification.collector_number
    return spec


def pack_card(card: UserTrackedCards) -> dict:
    """
    Packs a card dictionary into a standardized format for messaging.

    Args:
        card (dict): A dictionary representing a card, potentially including
                     'name', 'amount', and 'specifications'.

    Returns:
        dict: A dictionary containing the packed card data, including
              'card' (CardSchema), 'amount', and 'specifications'
              (list of CardSpecificationSchema).
    """

    packed = {"card": {"name": card.card_name},
              "amount": card.amount,
              "card_specs": []}
    for spec in card.specifications:
        packed["card_specs"].append(pack_specifications(spec))
    return packed
