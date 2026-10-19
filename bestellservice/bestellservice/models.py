"""Eingabemodelle der HTTP-Schnittstelle (Pydantic)."""

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ItemIn(Strict):
    sku: str
    quantity: int = Field(default=1, ge=1)


class CouponIn(Strict):
    code: str


class CustomerIn(Strict):
    name: str
    email: str
    type: str = "private"


class AddressIn(Strict):
    name: str
    street: str
    postal_code: str
    city: str
    country: str = "DE"


class OrderIn(Strict):
    cart_id: int
    customer: CustomerIn
    address: AddressIn


class StatusIn(Strict):
    status: str


class StockIn(Strict):
    on_hand: int
