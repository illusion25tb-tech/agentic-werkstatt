"""Fachliche Fehler. Die API übersetzt sie in HTTP-Antworten."""


class ShopError(Exception):
    """Basisklasse. `status` ist der HTTP-Statuscode."""

    status = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFound(ShopError):
    status = 404


class OutOfStock(ShopError):
    status = 409


class InvalidState(ShopError):
    status = 409


class ValidationFailed(ShopError):
    status = 422
