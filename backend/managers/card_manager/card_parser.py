import re


def parse_card_list(string_list: str):
    """
    Parses a list of card specifications and returns filtering conditions.
    Each card is parsed into a dictionary with filtering criteria.
    """
    parsed_cards = []
    pattern = r"^(\d+)\s+(.+?)(?:\s+\((\w+)\))?(?:\s+([\w-]+))?\s*(F|E|N/A)?$"

    for line in string_list.split("\n"):
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        match = re.match(pattern, line)
        if match:
            amount, card_name, set_code, collector_id, finish = match.groups()
            finish_map = {
                "F": "foil",
                "E": "etched",
                "N/A": "N/A",
                None: "normal",  # Default if not specified
            }
            parsed_cards.append(
                {
                    "amount": int(amount),
                    "card_name": card_name,
                    "set_code": set_code,  # None if not provided
                    "collector_id": collector_id,  # None if not provided
                    "finish": finish_map.get(finish, "normal"),  # Map finish
                }
            )
        else:
            print(f"Invalid card format: {line}")

    return parsed_cards
