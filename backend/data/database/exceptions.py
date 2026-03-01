"""Custom exception classes for the data layer."""


class InvalidSpecificationError(ValueError):
    """Raised when an invalid card specification is provided."""

    pass


class InvalidMessageError(ValueError):
    """Raised when an invalid message is provided to the socket manager."""

    pass
