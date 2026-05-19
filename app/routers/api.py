"""API router — JSON endpoints for dashboard data.

All endpoints return unformatted numeric values (``float``).
Formatting (currency, percentage) is the frontend's responsibility.

Dependencies:
    Engines under ``src/forecasting``, ``src/cashflow``, ``src/kpis``,
    ``src/data_generation``.  When an engine is not yet implemented the
    endpoint responds ``501 Not Implemented`` with a plain-text hint.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["api"])


# ── pydantic models ────────────────────────────────────────────────────────


class OverviewResponse(BaseModel):
    """Cards and summary data for the Overview page."""

    receita_12m: float = Field(..., description="Total revenue last 12 months (BRL)")
    crescimento_yoy: float = Field(..., description="Year-over-year growth (fraction)")
    saldo_projetado_final: float = Field(..., description="Projected ending cash balance")
    menor_saldo_projetado: float = Field(..., description="Lowest projected cash balance")
    estoque_atual: float = Field(..., description="Current inventory value")
    divida_total: float = Field(..., description="Total debt outstanding")
    ncg: float = Field(..., description="Necessidade de Capital de Giro")
    pmr: float = Field(..., description="Prazo Médio de Recebimento (days)")
    pme: float = Field(..., description="Prazo Médio de Estoque (days)")
    pmp: float = Field(..., description="Prazo Médio de Pagamento (days)")
    ciclo_financeiro: float = Field(..., description="PMR + PME - PMP (days)")


class ForecastPoint(BaseModel):
    """Single forecast data point."""

    data_mes: str = Field(..., description="Month (YYYY-MM-DD)")
    forecast_base: float
    forecast_otimista: float
    forecast_pessimista: float


class ForecastResponse(BaseModel):
    """Forecast endpoint response."""

    historico: List[ForecastPoint] = Field(..., description="Historical data points")
    forecast: List[ForecastPoint] = Field(..., description="Projected data points")


class CashflowDay(BaseModel):
    """Single day in the cash flow projection."""

    data: str = Field(..., description="Date (YYYY-MM-DD)")
    entradas_previstas: float
    saidas_previstas: float
    saldo_inicial_dia: float
    saldo_final_dia: float
    observacao: str = Field(default="Caixa normal")


class WorkingCapitalResponse(BaseModel):
    """Working capital components and metrics."""

    contas_receber: float
    contas_pagar: float
    estoque: float
    ncg: float = Field(..., description="AR + Estoque - AP")
    pmr: float
    pme: float
    pmp: float
    ciclo_financeiro: float = Field(..., description="PMR + PME - PMP")


class DebtPoint(BaseModel):
    """Single month in the debt evolution."""

    data_mes: str
    tipo_divida: str
    saldo_devedor: float
    juros_mes: float
    amortizacao: float


class DebtResponse(BaseModel):
    """Debt endpoint response."""

    divida_total: float
    divida_por_tipo: Dict[str, float]
    juros_mensais: float
    divida_receita_anualizada: float = Field(
        ..., description="Dívida total / receita anualizada"
    )
    cobertura_juros: float = Field(
        ..., description="EBITDA estimado / juros"
    )
    evolucao: List[DebtPoint]


# ── engine imports (graceful fallback) ─────────────────────────────────────

try:
    from forecasting.revenue_forecast import RevenueForecast
except ImportError:  # pragma: no cover
    RevenueForecast = None  # type: ignore[assignment,misc]

try:
    from cashflow.cashflow_projection import CashflowProjection
except ImportError:  # pragma: no cover
    CashflowProjection = None  # type: ignore[assignment,misc]

try:
    from kpis.financial_kpis import FinancialKPIs
except ImportError:  # pragma: no cover
    FinancialKPIs = None  # type: ignore[assignment,misc]

try:
    from data_generation.synthetic_generator import generate_all
except ImportError:  # pragma: no cover
    generate_all = None  # type: ignore[assignment,misc]


def _check_engine(engine: Any, name: str) -> None:
    """Raise ``HTTPException(501)`` if *engine* is ``None``."""
    if engine is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=501,
            detail=f"Engine '{name}' not implemented yet. "
            "Check the project roadmap for availability.",
        )


# ── helper: load data ──────────────────────────────────────────────────────


def _load_data(seed: int = 42) -> dict[str, Any]:
    """Load synthetic data from disk, falling back to in-memory generation."""
    from pathlib import Path

    from utils.io import read_csv

    data_dir = Path("data/synthetic")
    datasets: dict[str, Any] = {}

    if data_dir.exists():
        for csv_file in sorted(data_dir.glob("*.csv")):
            name = csv_file.stem
            try:
                datasets[name] = read_csv(str(csv_file))
            except Exception:
                pass

    # Fallback: generate in-memory if files not found
    if not datasets and generate_all is not None:
        datasets = generate_all(seed=seed, output_dir="data/synthetic/")

    return datasets


# ── endpoints ──────────────────────────────────────────────────────────────


@router.get("/overview", response_model=OverviewResponse)
def overview() -> Any:
    """Return summary cards for the Overview dashboard."""
    _check_engine(FinancialKPIs, "financial_kpis")
    datasets = _load_data()

    kpis = FinancialKPIs(datasets)

    return OverviewResponse(
        receita_12m=kpis.receita_ultimos_12m(),
        crescimento_yoy=kpis.crescimento_yoy(),
        saldo_projetado_final=0.0,  # needs cashflow projection (issue #6)
        menor_saldo_projetado=0.0,
        estoque_atual=kpis.estoque_total(),
        divida_total=kpis.divida_total(),
        ncg=kpis.ncg(),
        pmr=kpis.prazo_medio_recebimento(),
        pme=kpis.prazo_medio_estoque(),
        pmp=kpis.prazo_medio_pagamento(),
        ciclo_financeiro=kpis.ciclo_financeiro(),
    )


@router.get("/forecast", response_model=ForecastResponse)
def forecast(
    scenario: str = Query("base", description="base | otimista | pessimista"),
    horizon: int = Query(12, ge=1, le=24, description="Months to forecast"),
) -> Any:
    """Return historical revenue + forecast for the selected scenario."""
    _check_engine(RevenueForecast, "revenue_forecast")
    datasets = _load_data()

    engine = RevenueForecast(datasets["faturamento_historico"])
    historico_raw = engine.historico()
    forecast_raw = engine.forecast(horizon=horizon)

    # Select scenario column
    col = {
        "base": "forecast_base",
        "otimista": "forecast_otimista",
        "pessimista": "forecast_pessimista",
    }.get(scenario, "forecast_base")

    # Map historical points
    historico = [
        ForecastPoint(
            data_mes=str(row["data_mes"]),
            forecast_base=row.get("faturamento", 0.0),
            forecast_otimista=row.get("faturamento", 0.0) * 1.1,
            forecast_pessimista=row.get("faturamento", 0.0) * 0.9,
        )
        for _, row in historico_raw.iterrows()
    ]

    # Map forecast points
    forecast_pts = [
        ForecastPoint(
            data_mes=str(row["data_mes"]),
            forecast_base=row.get("forecast_base", 0.0),
            forecast_otimista=row.get("forecast_otimista", 0.0),
            forecast_pessimista=row.get("forecast_pessimista", 0.0),
        )
        for _, row in forecast_raw.iterrows()
    ]

    return ForecastResponse(historico=historico, forecast=forecast_pts)


@router.get("/cashflow")
def cashflow(
    horizon: int = Query(90, ge=30, le=180, description="Days to project"),
    saldo_inicial: float = Query(0.0, description="Starting cash balance (BRL)"),
    scenario: str = Query("base", description="Revenue scenario"),
    prazo_medio_recebimento: int | None = Query(
        None, ge=0, description="Override collections delay (days)"
    ),
) -> list[CashflowDay]:
    """Return daily cash flow projection."""
    _check_engine(CashflowProjection, "cashflow_projection")
    datasets = _load_data()

    engine = CashflowProjection(
        contas_receber=datasets.get("contas_receber"),
        contas_pagar=datasets.get("contas_pagar"),
        forecast=datasets.get("forecast_faturamento"),
        saldo_inicial=saldo_inicial,
    )

    proj = engine.project(horizon=horizon)

    return [
        CashflowDay(
            data=str(row["data"]),
            entradas_previstas=float(row.get("entradas_previstas", 0)),
            saidas_previstas=float(row.get("saidas_previstas", 0)),
            saldo_inicial_dia=float(row.get("saldo_inicial_dia", 0)),
            saldo_final_dia=float(row.get("saldo_final_dia", 0)),
            observacao=str(row.get("observacao", "Caixa normal")),
        )
        for _, row in proj.iterrows()
    ]


@router.get("/working-capital", response_model=WorkingCapitalResponse)
def working_capital() -> Any:
    """Return working capital components and cycle metrics."""
    _check_engine(FinancialKPIs, "financial_kpis")
    datasets = _load_data()

    kpis = FinancialKPIs(datasets)

    return WorkingCapitalResponse(
        contas_receber=kpis.contas_receber_saldo(),
        contas_pagar=kpis.contas_pagar_saldo(),
        estoque=kpis.estoque_total(),
        ncg=kpis.ncg(),
        pmr=kpis.prazo_medio_recebimento(),
        pme=kpis.prazo_medio_estoque(),
        pmp=kpis.prazo_medio_pagamento(),
        ciclo_financeiro=kpis.ciclo_financeiro(),
    )


@router.get("/debt", response_model=DebtResponse)
def debt() -> Any:
    """Return debt overview and evolution."""
    _check_engine(FinancialKPIs, "financial_kpis")
    datasets = _load_data()

    kpis = FinancialKPIs(datasets)

    return DebtResponse(
        divida_total=kpis.divida_total(),
        divida_por_tipo=kpis.divida_por_tipo(),
        juros_mensais=kpis.juros_mensais(),
        divida_receita_anualizada=kpis.divida_receita_anualizada(),
        cobertura_juros=kpis.cobertura_juros(),
        evolucao=[],
    )
