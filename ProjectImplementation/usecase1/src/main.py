"""FastAPI application factory.

Registers middleware, exception handlers, and all routers.
Configures structured logging on startup.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import TraceIDMiddleware
from src.api.routers import enrichment, health, leads
from src.core.config import get_settings
from src.core.exceptions import BaseAppException
from src.core.logging import configure_logging, get_logger

_settings = get_settings()
configure_logging(log_level=_settings.LOG_LEVEL)
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="Jewelry AI — Lead Automation Platform",
        description="AI-powered lead automation for Shivam Jewels.",
        version=_settings.APP_VERSION,
        docs_url="/docs" if _settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if _settings.APP_ENV != "production" else None,
    )

    # ── Middleware (applied in reverse order — last registered runs first) ──
    app.add_middleware(TraceIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if _settings.APP_ENV == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", None)
        logger.error(
            "Application exception code=%s message=%s status=%d",
            exc.code,
            exc.message,
            exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.message,
                "code": exc.code,
                "detail": exc.detail,
                "trace_id": trace_id,
            },
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(leads.router)
    app.include_router(enrichment.router)

    # ── Startup log ───────────────────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info(
            "Jewelry AI starting up env=%s version=%s",
            _settings.APP_ENV,
            _settings.APP_VERSION,
        )

    return app


app = create_app()
