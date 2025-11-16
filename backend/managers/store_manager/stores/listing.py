from typing import Any, Dict


class Listing:
    """
    Represents a product listing with details such as name, set code,
    collector number, finish, price, condition, and URL.
    Attributes:
        url (str): The URL of the listing.
        name (str): The name of the product.
        set_code (str): The code of the set, always stored in uppercase.
        collector_number (str): The collector number of the product.
        finish (str): The finish type of the product.
        price (float): The price of the product.
        condition (str): The condition of the product.

    Properties:
        set_code (str): Gets or sets the set code, ensuring it is uppercase.
        id (dict): Gets or sets a dictionary containing name, price,
        condition, and URL.
        details (dict): Gets or sets a dictionary containing set_code,
        collector_number, and finish.

    Methods:
        to_dict() -> dict: Returns a dictionary representation of the listing.
        __eq__(other) -> bool: Checks equality with another Listing instance
        based on id.
        __hash__() -> int: Returns a hash value for the listing based on its
        attributes.
    """

    def __init__(self):
        self.url = ""
        self.name = ""
        self.set_code = ""
        self.collector_number = ""
        self.finish = ""
        self.price = 0.0
        self.condition = ""
        self.stock = 0

    @property
    def set_code(self) -> str:
        return self._set_code

    @set_code.setter
    def set_code(self, value: str):
        self._set_code = value.upper() if value else ""

    @property
    def id(self) -> dict:
        return {
            "name": self.name,
            "price": self.price,
            "condition": self.condition,
            "url": self.url,
        }

    @id.setter
    def id(self, value: dict):
        self.name = value.get("name", "")
        self.price = value.get("price", 0.0)
        self.condition = value.get("condition", "")
        self.url = value.get("url", "")

    @property
    def details(self) -> Dict[str, Any]:
        return {
            "set_code": self.set_code,
            "collector_number": self.collector_number,
            "finish": self.finish,
        }

    @details.setter
    def details(self, value: dict):
        self.set_code = value.get("set_code", "")
        self.collector_number = value.get("collector_number", "")
        self.finish = value.get("finish", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "name": self.name,
            "set_code": self.set_code,
            "collector_number": self.collector_number,
            "finish": self.finish,
            "price": self.price,
            "condition": self.condition,
        }

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Listing):
            return False
        return self.id == other.id and self.details == other.details

    def __hash__(self) -> int:
        return hash(
            (
                self.name,
                self.set_code,
                self.collector_number,
                self.finish,
                self.price,
                self.condition,
            )
        )
