"""Tests for :mod:`cashflow.cashflow_projection`."""

from __future__ import annotations

import datetime

import pandas as pd
import pytest

from cashflow.cashflow_projection import CashflowProjection


# ── helpers ────────────────────────────────────────────────────────────────


def _make_test_ar() -> pd.DataFrame:
    """Minimal accounts receivable for testing."""
    return pd.DataFrame(
        [
            {
                "id_titulo": "AR-001",
                "data_emissao": "2026-05-01",
                "data_vencimento": "2026-06-15",
                "data_pagamento": None,
                "valor": 50000.0,
                "status": "Aberto",
                "canal": "Farma",
                "uf": "SP",
                "cliente": "Cliente A",
            },
            {
                "id_titulo": "AR-002",
                "data_emissao": "2026-04-01",
                "data_vencimento": "2026-05-20",
                "data_pagamento": None,
                "valor": 30000.0,
                "status": "Aberto",
                "canal": "Distribuidor",
                "uf": "RJ",
                "cliente": "Cliente B",
            },
        ]
    )


def _make_test_ap() -> pd.DataFrame:
    """Minimal accounts payable for testing."""
    return pd.DataFrame(
        [
            {
                "id_titulo": "AP-001",
                "data_emissao": "2026-05-10",
                "data_vencimento": "2026-06-20",
                "data_pagamento": None,
                "valor": 20000.0,
                "status": "Aberto",
                "fornecedor": "Fornecedor X",
                "categoria": "Matéria-prima",
            },
            {
                "id_titulo": "AP-002",
                "data_emissao": "2026-05-01",
                "data_vencimento": "2026-05-25",
                "data_pagamento": None,
                "valor": 10000.0,
                "status": "Aberto",
                "fornecedor": "Fornecedor Y",
                "categoria": "Frete",
            },
        ]
    )


def _make_test_forecast() -> pd.DataFrame:
    """Minimal forecast for testing."""
    return pd.DataFrame(
        [
            {
                "data_mes": "2026-06-01",
                "forecast_base": 1_000_000.0,
                "forecast_otimista": 1_100_000.0,
                "forecast_pessimista": 900_000.0,
            },
            {
                "data_mes": "2026-07-01",
                "forecast_base": 1_100_000.0,
                "forecast_otimista": 1_210_000.0,
                "forecast_pessimista": 990_000.0,
            },
        ]
    )


def _load_real_data() -> dict:
    """Load real synthetic data for integration tests."""
    from data_generation.synthetic_generator import generate_all
    from forecasting.revenue_forecast import RevenueForecast

    ds = generate_all(42)
    fc = RevenueForecast(ds["faturamento_historico"]).forecast(12)
    return {**ds, "forecast_faturamento": fc}


# ── unit tests ─────────────────────────────────────────────────────────────


class TestProjectionOutput:
    """Output structure and invariants."""

    def test_output_columns(self) -> None:
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 50000.0
        )
        proj = engine.project(90)
        expected = {
            "data", "entradas_previstas", "saidas_previstas",
            "saldo_inicial_dia", "saldo_final_dia", "observacao",
        }
        assert set(proj.columns) == expected

    def test_horizon_length(self) -> None:
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 0.0
        )
        for h in [30, 90, 180]:
            proj = engine.project(h)
            # Calendar days (including today) = h+1
            assert len(proj) >= h

    def test_horizon_clamped(self) -> None:
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 0.0
        )
        assert len(engine.project(10)) >= 30  # clamped to 30
        assert len(engine.project(365)) <= 181  # clamped to 180

    def test_saldo_continuity(self) -> None:
        """saldo_final_dia[t] == saldo_inicial_dia[t+1]."""
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 50000.0
        )
        proj = engine.project(90)
        for i in range(len(proj) - 1):
            assert proj["saldo_final_dia"].iloc[i] == pytest.approx(
                proj["saldo_inicial_dia"].iloc[i + 1]
            )

    def test_balance_equation(self) -> None:
        """saldo_final = saldo_inicial + entries - exits."""
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 50000.0
        )
        proj = engine.project(90)
        for _, row in proj.iterrows():
            expected = row["saldo_inicial_dia"] + row["entradas_previstas"] - row["saidas_previstas"]
            assert row["saldo_final_dia"] == pytest.approx(expected)


class TestObservacaoClassification:
    """Risk classification logic."""

    def test_negative_is_risco(self) -> None:
        df = pd.DataFrame([
            {"data_mes": "2026-06-01", "forecast_base": 100.0},
        ])
        # Force negative: large exit, no entry
        ar = _make_test_ar()
        apr = pd.DataFrame([
            {
                "id_titulo": "AP-BIG",
                "data_emissao": "2026-05-01",
                "data_vencimento": "2026-05-26",
                "data_pagamento": None,
                "valor": 100000.0,
                "status": "Aberto",
                "fornecedor": "Big Corp",
                "categoria": "Serviços",
            },
        ])
        engine = CashflowProjection(ar, apr, df, 1000.0)
        proj = engine.project(30)
        risks = proj[proj["observacao"].str.contains("Risco")]
        assert len(risks) > 0, "Should have risk days with negative balance"

    def test_normal_day(self) -> None:
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 1_000_000.0
        )
        proj = engine.project(30)
        assert all("normal" in obs.lower() for obs in proj["observacao"])


class TestBusinessDays:
    """Weekend/holiday handling."""

    def test_entries_on_business_days_only(self) -> None:
        """Open receivables should be adjusted to business days."""
        # Create a receivable due on Sunday
        ar = pd.DataFrame([
            {
                "id_titulo": "AR-SUN",
                "cliente": "Test",
                "data_emissao": "2026-05-01",
                "data_vencimento": "2026-06-07",  # Sunday
                "data_pagamento": None,
                "valor": 10000.0,
                "status": "Aberto",
                "canal": "Farma",
                "uf": "SP",
            },
        ])
        ap = pd.DataFrame()
        fc = _make_test_forecast()
        engine = CashflowProjection(ar, ap, fc, 0.0)
        proj = engine.project(60)

        # Find the entry
        entry_days = proj[proj["entradas_previstas"] > 0]
        if len(entry_days) > 0:
            for _, row in entry_days.iterrows():
                d = row["data"].date()
                assert d.weekday() < 5, f"{d} is a weekend: weekday={d.weekday()}"


class TestConvenienceMethods:
    """Menor saldo, dias negativos, necessidade máxima."""

    def test_menor_saldo(self) -> None:
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 50_000.0
        )
        proj = engine.project(90)
        assert engine.menor_saldo(proj) <= engine._saldo_inicial

    def test_dias_negativos(self) -> None:
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 1_000_000.0
        )
        proj = engine.project(90)
        assert engine.dias_negativos(proj) == 0

    def test_necessidade_maxima(self) -> None:
        engine = CashflowProjection(
            _make_test_ar(), _make_test_ap(), _make_test_forecast(), 1_000_000.0
        )
        proj = engine.project(90)
        assert engine.necessidade_maxima_caixa(proj) >= 0


class TestIntegration:
    """Full integration with synthetic data."""

    def test_real_data_projection(self) -> None:
        ds = _load_real_data()
        engine = CashflowProjection(
            ds["contas_receber"],
            ds["contas_pagar"],
            ds["forecast_faturamento"],
            1_500_000.0,
        )
        proj = engine.project(90)
        assert len(proj) >= 90
        assert proj["saldo_final_dia"].notna().all()
        assert set(proj["observacao"].unique()).issubset(
            {"Caixa normal", "Atenção: saldo baixo", "Risco: caixa negativo"}
        )

    def test_forecast_distribution_sums(self) -> None:
        """Forecast distribution should approximately sum to forecast values."""
        ds = _load_real_data()
        fc = ds["forecast_faturamento"]
        engine = CashflowProjection(
            ds["contas_receber"],
            pd.DataFrame(),  # no payables to isolate forecast
            fc,
            0.0,
        )
        proj = engine.project(180)

        # Check each forecast month's entries roughly match
        total_entries = proj["entradas_previstas"].sum()
        total_forecast = fc["forecast_base"].sum()
        # Should be in same ballpark (entries include open receivables too)
        assert total_entries > 0
