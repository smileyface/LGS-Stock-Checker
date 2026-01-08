from schema.blocks import (CardSchema,
                           CardSpecificationSchema,
                           SetSchema,
                           FinishSchema
                           )


def pack_specifications(specifications: list[dict]) -> list[dict]:
    """
    Packs a list of specification dictionaries into a standardized format for messaging.

    Args:
        specifications (list[dict]): A list of dictionaries, where each
                                     dictionary represents a card specification.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary is a
                    CardSpecificationSchema model_dump.
    """
    specs = []
    for spec in specifications:
        if not isinstance(spec, dict):
            continue
        if "set_code" in spec and spec["set_code"] is not None:
            spec["set_code"] = SetSchema(code=spec["set_code"]).model_dump()
        else:
            del spec["set_code"]
        if "finish" in spec and spec["finish"] is not None:
            spec["finish"] = FinishSchema(name=spec["finish"]).model_dump()
        else:
            del spec["finish"]
        if "collector_number" in spec and spec["collector_number"] is not None:
            spec["collector_number"] = spec["collector_number"]
        else:
            del spec["collector_number"]

        specs.append(CardSpecificationSchema(**spec).model_dump())
    return specs


def pack_card(name: str,
              amount: int,
              specifications: list[dict] = [],
              **kwargs) -> dict:
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
    specifications = pack_specifications(specifications)

    card_name_obj = CardSchema(name=name).model_dump()

    packed = {"card": card_name_obj, "amount": amount}
    if specifications:
        packed["card_specs"] = specifications
    return packed
