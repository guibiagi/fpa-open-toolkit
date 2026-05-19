"""Pages router — HTML routes rendered with Jinja2 templates.

Each route corresponds to a page in the FP&A Open Toolkit web interface.
Templates extend ``base.html`` and consume data from ``/api/*`` endpoints
via HTMX partial updates.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

TEMPLATES = Jinja2Templates(directory="app/templates")


def _render_or_not_found(request: Request, template: str) -> HTMLResponse:
    """Try to render *template*, fall back to a friendly 404 page."""
    try:
        return TEMPLATES.TemplateResponse(request, template, {"request": request})
    except Exception:
        return TEMPLATES.TemplateResponse(
            request,
            "index.html",
            {
                "request": request,
                "error": f"Template '{template}' not yet implemented",
            },
        )


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Overview dashboard — cards, revenue chart, forecast preview, cashflow, NCG."""
    return _render_or_not_found(request, "index.html")


@router.get("/forecast", response_class=HTMLResponse)
def forecast_page(request: Request) -> HTMLResponse:
    """Revenue forecast page — historical + projected revenue."""
    return _render_or_not_found(request, "forecast.html")


@router.get("/cashflow", response_class=HTMLResponse)
def cashflow_page(request: Request) -> HTMLResponse:
    """Cash flow projection — daily balance, entries, exits, alerts."""
    return _render_or_not_found(request, "cashflow.html")


@router.get("/working-capital", response_class=HTMLResponse)
def working_capital_page(request: Request) -> HTMLResponse:
    """Working capital — NCG, PMR, PME, PMP, estoque breakdown."""
    return _render_or_not_found(request, "working_capital.html")


@router.get("/debt", response_class=HTMLResponse)
def debt_page(request: Request) -> HTMLResponse:
    """Debt analysis — total, by type, amortization, coverage."""
    return _render_or_not_found(request, "debt.html")


@router.get("/explorer", response_class=HTMLResponse)
def explorer_page(request: Request) -> HTMLResponse:
    """Data explorer — browse synthetic datasets with filters."""
    return _render_or_not_found(request, "explorer.html")
