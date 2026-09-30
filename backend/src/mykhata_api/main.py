from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from mykhata_api.db import make_engine, session_factory
from mykhata_api.deps import CSRF_HEADER
from mykhata_api.routes import auth, budgets, model, statements, transactions
from mykhata_api.security import RateLimiter
from mykhata_ml import export
from mykhata_ml.config import load_config, path

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
FIELD_MESSAGES = {
    "email": "Enter a valid email address you can receive mail at.",
    "password": "Use a password of 8 to 128 characters.",
    "name": "Enter your name (up to 80 characters).",
    "amount": "Enter an amount above ₹0.",
    "date": "Enter a valid date.",
    "narration": "Describe the transaction in 2 to 512 characters.",
}
SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


def create_app(overrides: dict[str, Any] | None = None) -> FastAPI:
    cfg = load_config()
    settings = cfg["api"] | (overrides or {})

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database = path(settings["database"])
        database.parent.mkdir(parents=True, exist_ok=True)
        engine = make_engine(settings.get("database_url") or f"sqlite:///{database}")
        app.state.settings = settings
        app.state.sessionmaker = session_factory(engine)
        app.state.model = export.load(path(cfg["output"]["artifacts"]))
        app.state.login_limiter = RateLimiter(settings["login_attempts"], settings["login_window_seconds"])
        yield
        engine.dispose()

    app = FastAPI(title="MyKhata API", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if request.method in UNSAFE_METHODS and request.headers.get(CSRF_HEADER) != "1":
            response = JSONResponse({"detail": "Missing request header"}, status_code=403)
        else:
            response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    @app.exception_handler(RequestValidationError)
    async def friendly_validation(_: Request, exc: RequestValidationError):
        error = exc.errors()[0] if exc.errors() else {}
        field = str(error.get("loc", ["", ""])[-1])
        message = FIELD_MESSAGES.get(field) or str(error.get("msg", "Check the form and try again.")).removeprefix("Value error, ")
        return JSONResponse({"detail": message}, status_code=422)

    for router in (auth.router, transactions.router, statements.router, budgets.router, model.router):
        app.include_router(router)
    return app


app = create_app()
