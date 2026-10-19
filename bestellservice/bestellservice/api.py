"""HTTP-Routen des bestellservice."""

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from . import cart, catalog, inventory, invoice, labels, orders
from .models import (
    CouponIn,
    ItemIn,
    OrderIn,
    StatusIn,
    StockIn,
)

router = APIRouter()


def _conn(request: Request):
    return request.app.state.conn


def _clock(request: Request):
    return request.app.state.clock


# ------------------------------------------------------------
# Katalog und Lager
# ------------------------------------------------------------


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/articles")
def get_articles(
    request: Request,
    q: str | None = None,
    category: str | None = None,
) -> list[dict]:
    conn = _conn(request)
    if q:
        found = catalog.search(conn, q)
    else:
        found = catalog.list_articles(conn, category)
    return [a.to_dict() for a in found]


@router.get("/articles/{sku}")
def get_article(request: Request, sku: str) -> dict:
    return catalog.get_article(_conn(request), sku).to_dict()


@router.get("/categories")
def get_categories(request: Request) -> list[str]:
    return catalog.categories(_conn(request))


@router.get("/stock/{sku}")
def get_stock(request: Request, sku: str) -> dict:
    return inventory.stock_info(_conn(request), sku)


@router.put("/stock/{sku}")
def put_stock(
    request: Request, sku: str, body: StockIn
) -> dict:
    return inventory.set_on_hand(
        _conn(request), sku, body.on_hand
    )


# ------------------------------------------------------------
# Warenkorb
# ------------------------------------------------------------


@router.post("/carts", status_code=201)
def post_cart(request: Request) -> dict:
    cart_id = cart.create_cart(_conn(request), _clock(request))
    return {"cart_id": cart_id}


@router.get("/carts/{cart_id}")
def get_cart(
    request: Request, cart_id: int, country: str = "DE"
) -> dict:
    return cart.cart_summary(_conn(request), cart_id, country)


@router.post("/carts/{cart_id}/items", status_code=201)
def post_item(request: Request, cart_id: int, body: ItemIn):
    conn = _conn(request)
    item_id = cart.add_item(
        conn, cart_id, body.sku, body.quantity
    )
    return {"item_id": item_id}


@router.delete("/carts/{cart_id}/items/{item_id}")
def delete_item(
    request: Request, cart_id: int, item_id: int
) -> dict:
    cart.remove_item(_conn(request), cart_id, item_id)
    return {"deleted": item_id}


@router.post("/carts/{cart_id}/coupon")
def post_coupon(
    request: Request, cart_id: int, body: CouponIn
) -> dict:
    coupon = cart.apply_coupon(
        _conn(request), cart_id, body.code
    )
    return {"code": coupon["code"]}


# ------------------------------------------------------------
# Bestellungen
# ------------------------------------------------------------


@router.post("/orders", status_code=201)
def post_order(request: Request, body: OrderIn) -> dict:
    return orders.create_order(
        _conn(request),
        body.cart_id,
        body.customer.model_dump(),
        body.address.model_dump(),
        _clock(request),
    )


@router.get("/orders")
def get_orders(request: Request) -> list[dict]:
    return orders.list_orders(_conn(request))


@router.get("/orders/export.csv")
def get_orders_csv(request: Request):
    text = orders.export_csv(_conn(request))
    return PlainTextResponse(text, media_type="text/csv")


@router.get("/orders/{order_id}")
def get_order(request: Request, order_id: int) -> dict:
    return orders.get_order(_conn(request), order_id)


@router.post("/orders/{order_id}/status")
def post_status(
    request: Request, order_id: int, body: StatusIn
) -> dict:
    return orders.set_status(
        _conn(request), order_id, body.status, _clock(request)
    )


@router.get("/orders/{order_id}/history")
def get_history(request: Request, order_id: int):
    return orders.status_history(_conn(request), order_id)


@router.get("/orders/{order_id}/confirmation")
def get_confirmation(request: Request, order_id: int):
    order = orders.get_order(_conn(request), order_id)
    return PlainTextResponse(orders.confirmation_text(order))


@router.get("/orders/{order_id}/invoice")
def get_invoice(request: Request, order_id: int) -> dict:
    return invoice.build_invoice(_conn(request), order_id)


# ------------------------------------------------------------
# Versandlabels
# ------------------------------------------------------------


@router.post("/orders/{order_id}/label", status_code=201)
def post_label(request: Request, order_id: int) -> dict:
    return orders.create_label(
        _conn(request), order_id, _clock(request)
    )


@router.get("/orders/{order_id}/label")
def get_label(request: Request, order_id: int) -> dict:
    return labels.get_label(_conn(request), order_id)
