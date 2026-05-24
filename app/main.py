"""FP&A Open Toolkit — FastAPI application entry point.

Start with::

    uvicorn app.main:app --reload --port 8000
    # or
    make app

Then open http://localhost:8000/docs for the OpenAPI schema.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.routers import api, export, pages

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _setup_logging() -> None:
    """Configure structured logging for the application."""
    level = logging.DEBUG if settings.is_development else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)-7s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers in dev
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger("fpa")
    logger.info(
        "FP&A Open Toolkit starting (env=%s seed=%d data_dir=%s)",
        settings.env,
        settings.seed,
        settings.data_dir,
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown events."""
    _setup_logging()
    logger = logging.getLogger("fpa")

    # Ensure output directory
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)

    # Pre-generate synthetic data if missing
    data_path = Path(settings.data_dir)
    if not data_path.exists() or not list(data_path.glob("*.csv")):
        logger.info("Generating synthetic data (seed=%d)…", settings.seed)
        try:
            from data_generation.synthetic_generator import generate_all

            generate_all(seed=settings.seed, output_dir=settings.data_dir)
            logger.info("Synthetic data ready.")
        except Exception as exc:
            logger.warning("Could not auto-generate data: %s", exc)

    logger.info("Server ready at http://%s:%d", settings.host, settings.port)
    yield
    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


app = FastAPI(
    title="FP&A Open Toolkit",
    description=(
        "Financial Planning & Analysis toolkit for industrial SMEs. "
        "Synthetic data, revenue forecasting, cash flow projection, "
        "KPIs, and export — all open source."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)


# ── Static files ───────────────────────────────────────────────────────────


static_path = Path(settings.static_dir)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ── Templates ──────────────────────────────────────────────────────────────


templates = Jinja2Templates(directory=settings.templates_dir)


# ── Routers ────────────────────────────────────────────────────────────────


app.include_router(pages.router)
app.include_router(api.router)
app.include_router(export.router)


# ── Exception handlers ─────────────────────────────────────────────────────


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a JSON-friendly 404."""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Not found",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a JSON-friendly 500, logging the error."""
    logging.getLogger("fpa").error(
        "Internal error on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=settings.is_development,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
        },
    )


# ── Health check ───────────────────────────────────────────────────────────


@app.get("/health", response_class=PlainTextResponse, tags=["system"])
def health() -> str:
    """Return OK if the server is alive."""
    return "OK"


@app.get("/health/ready", response_class=PlainTextResponse, tags=["system"])
def readiness() -> PlainTextResponse:
    """Return OK if data is available and the server is ready to serve."""
    data_path = Path(settings.data_dir)
    if not data_path.exists() or not list(data_path.glob("*.csv")):
        return PlainTextResponse("Data not generated", status_code=503)
    return PlainTextResponse("OK")
