"""Einstiegspunkt: baut die FastAPI-App.

Start lokal mit:
    uvicorn bestellservice.main:app --reload
"""

from collections.abc import Callable
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import __version__, db
from .api import router
from .errors import ShopError


def create_app(
    db_path: str = ":memory:",
    clock: Callable[[], datetime] = datetime.now,
) -> FastAPI:
    """Neue App mit eigener Datenbank.

    `clock` lässt sich in Tests durch eine feste Uhr ersetzen.
    """
    app = FastAPI(
        title="bestellservice",
        version=__version__,
        description="Nordlicht Werkzeughandel GmbH (fiktiv)",
    )
    app.state.conn = db.connect(db_path)
    app.state.clock = clock

    @app.exception_handler(ShopError)
    def shop_error(request: Request, exc: ShopError):
        return JSONResponse(
            status_code=exc.status,
            content={"detail": exc.message},
        )

    app.include_router(router)
    return app


app = create_app()
