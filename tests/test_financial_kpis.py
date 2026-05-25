"""Tests for :mod:`kpis.financial_kpis`."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from kpis.financial_kpis import FinancialKPIs


def _load_real_data() -> dict:
    """Load real synthetic data for integration tests."""
    from data_generation.synthetic_generator import generate_all

    return generate_all(42)


# ── Revenue KPIs ────────────────────────────────────────────────────────────


class TestRevenue:
    def test_receita_ultimos_12m_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.receita_ultimos_12m()
        assert result > 0
        assert result > 40_000_000  # ~4.2M/mo * 12

    def test_crescimento_mensal_reasonable(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.crescimento_mensal()
        assert -0.50 < result < 0.50  # MoM growth within ±50%

    def test_crescimento_yoy_reasonable(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.crescimento_yoy()
        assert -0.50 < result < 0.50

    def test_media_movel_3m_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.media_movel_3m()
        assert result > 0

    def test_faturamento_mensal_dataframe(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        df = kpis.faturamento_mensal()
        assert len(df) >= 48
        assert "faturamento" in df.columns

    def test_crescimento_ytd(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.crescimento_ytd()
        assert isinstance(result, float)


# ── Working Capital KPIs ────────────────────────────────────────────────────


class TestWorkingCapital:
    def test_contas_receber_saldo_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.contas_receber_saldo()
        assert result > 0

    def test_contas_pagar_saldo_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.contas_pagar_saldo()
        assert result > 0

    def test_estoque_total_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.estoque_total()
        assert result > 0

    def test_ncg_formula(self) -> None:
        """NCG = AR + Inventory - AP."""
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        ncg = kpis.ncg()
        expected = (
            kpis.contas_receber_saldo()
            + kpis.estoque_total()
            - kpis.contas_pagar_saldo()
        )
        assert ncg == pytest.approx(expected)

    def test_prazo_medio_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        assert kpis.prazo_medio_recebimento() > 0
        assert kpis.prazo_medio_pagamento() > 0

    def test_pme_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.prazo_medio_estoque()
        assert result > 0
        assert result < 365  # Less than a year

    def test_ciclo_financeiro_formula(self) -> None:
        """Ciclo = PMR + PME - PMP."""
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        ciclo = kpis.ciclo_financeiro()
        expected = (
            kpis.prazo_medio_recebimento()
            + kpis.prazo_medio_estoque()
            - kpis.prazo_medio_pagamento()
        )
        assert ciclo == pytest.approx(expected, abs=0.1)  # round() may apply


# ── Debt KPIs ───────────────────────────────────────────────────────────────


class TestDebt:
    def test_divida_total_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.divida_total()
        assert result > 0

    def test_divida_por_tipo_three_types(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.divida_por_tipo()
        assert len(result) == 3  # Capital de giro, Financiamento, Investimento
        assert "Capital de giro" in result

    def test_juros_mensais_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.juros_mensais()
        assert result > 0

    def test_divida_receita_ratio(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.divida_receita_anualizada()
        assert 0 < result < 2.0  # Debt should be less than 2x revenue

    def test_cobertura_juros_positive(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        result = kpis.cobertura_juros()
        assert result > 0


# ── Cash KPIs ───────────────────────────────────────────────────────────────


class TestCash:
    def test_empty_cashflow_returns_zero(self) -> None:
        ds = _load_real_data()
        kpis = FinancialKPIs(ds)
        assert kpis.saldo_final_projetado() == 0.0
        assert kpis.menor_saldo_projetado() == 0.0
        assert kpis.dias_caixa_negativo() == 0

    def test_with_cashflow_data(self) -> None:
        """KPIs with actual cashflow projection data."""
        from cashflow.cashflow_projection import CashflowProjection
        from forecasting.revenue_forecast import RevenueForecast

        ds = _load_real_data()
        forecast_df = RevenueForecast(ds["faturamento_historico"]).forecast(12)

        engine = CashflowProjection(
            ds["contas_receber"],
            ds["contas_pagar"],
            forecast_df,
            1_500_000.0,
        )
        proj = engine.project(90)

        ds["fluxo_caixa_projetado"] = proj
        kpis = FinancialKPIs(ds)

        assert kpis.saldo_final_projetado() != 0.0
        assert kpis.menor_saldo_projetado() >= 0
        assert kpis.dias_caixa_negativo() == 0


# ── Edge cases ──────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_datasets(self) -> None:
        kpis = FinancialKPIs({})
        assert kpis.receita_ultimos_12m() == 0.0
        assert kpis.ncg() == 0.0
        assert kpis.divida_total() == 0.0
        assert kpis.cobertura_juros() == float("inf")
        assert kpis.divida_por_tipo() == {}

    def test_juros_zero_coverage(self) -> None:
        """cobertura_juros should handle zero interest."""
        ds = _load_real_data()
        # Zero out the juros
        ds["divida"]["juros_mes"] = 0.0
        kpis = FinancialKPIs(ds)
        result = kpis.cobertura_juros()
        assert result == float("inf")
