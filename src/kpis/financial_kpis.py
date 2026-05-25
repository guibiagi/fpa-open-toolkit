"""Financial KPIs calculator for FP&A Open Toolkit.

Implements spec v1.1 §7.4 — all required financial indicators:

Revenue:
    - Monthly revenue, MoM growth, YTD growth, 3-month moving average

Working Capital:
    - AR balance, AP balance, Inventory, NCG, Financial cycle (PMR+PME-PMP)

Debt:
    - Total debt, debt by type, monthly interest, Debt/Annualized Revenue,
      Interest coverage

Cash:
    - Projected ending balance, lowest balance, negative days, max cash need

Usage::

    from kpis.financial_kpis import FinancialKPIs

    kpis = FinancialKPIs(datasets)
    ncg = kpis.ncg()
    ciclo = kpis.ciclo_financeiro()
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


class FinancialKPIs:
    """Calculate all financial KPIs from synthetic datasets.

    Parameters
    ----------
    datasets:
        Dict of DataFrames from ``generate_all()``. Expected keys:
        ``faturamento_historico``, ``contas_receber``, ``contas_pagar``,
        ``estoque``, ``divida``, ``custo_vendas``.
        Also accepts ``forecast_faturamento`` and ``fluxo_caixa_projetado``
        when available.
    """

    def __init__(self, datasets: dict[str, pd.DataFrame]) -> None:
        self._fat = datasets.get("faturamento_historico", pd.DataFrame())
        self._ar = datasets.get("contas_receber", pd.DataFrame())
        self._ap = datasets.get("contas_pagar", pd.DataFrame())
        self._estoque = datasets.get("estoque", pd.DataFrame())
        self._divida = datasets.get("divida", pd.DataFrame())
        self._custo = datasets.get("custo_vendas", pd.DataFrame())
        self._forecast = datasets.get("forecast_faturamento", pd.DataFrame())
        self._cashflow = datasets.get("fluxo_caixa_projetado", pd.DataFrame())

        # Ensure date columns are datetime
        for df in [self._fat, self._ar, self._ap, self._estoque, self._divida, self._custo]:
            for col in df.columns:
                if "data" in col.lower():
                    df[col] = pd.to_datetime(df[col])

        # Pre-compute monthly aggregates
        self._monthly = self._build_monthly()

    # ── helpers ───────────────────────────────────────────────────────

    def _build_monthly(self) -> pd.DataFrame:
        """Build aggregated monthly revenue DataFrame."""
        if self._fat.empty or "faturamento" not in self._fat.columns:
            return pd.DataFrame(columns=["data_mes", "faturamento"])

        return (
            self._fat.groupby("data_mes")["faturamento"]
            .sum()
            .reset_index()
            .sort_values("data_mes")
            .reset_index(drop=True)
        )

    # ── Revenue KPIs ──────────────────────────────────────────────────

    def faturamento_mensal(self) -> pd.DataFrame:
        """Return monthly revenue DataFrame."""
        return self._monthly.copy()

    def receita_ultimos_12m(self) -> float:
        """Total revenue over the last 12 months."""
        if len(self._monthly) == 0:
            return 0.0
        recent = self._monthly.tail(12)
        return float(recent["faturamento"].sum())

    def crescimento_mensal(self) -> float:
        """Month-over-month growth rate (most recent month)."""
        if len(self._monthly) < 2:
            return 0.0
        current = self._monthly["faturamento"].iloc[-1]
        previous = self._monthly["faturamento"].iloc[-2]
        if previous == 0:
            return 0.0
        return float((current - previous) / previous)

    def crescimento_yoy(self) -> float:
        """Year-over-year growth (most recent 12m vs prior 12m)."""
        if len(self._monthly) < 24:
            return 0.0
        recent = self._monthly["faturamento"].iloc[-12:].sum()
        prior = self._monthly["faturamento"].iloc[-24:-12].sum()
        if prior == 0:
            return 0.0
        return float((recent - prior) / prior)

    def media_movel_3m(self) -> float:
        """3-month moving average of revenue."""
        if len(self._monthly) < 3:
            return 0.0
        return float(self._monthly["faturamento"].tail(3).mean())

    def crescimento_ytd(self) -> float:
        """Year-to-date growth (current year months vs same months last year)."""
        if len(self._monthly) < 13:
            return 0.0

        df = self._monthly.copy()
        df["year"] = df["data_mes"].dt.year
        df["month"] = df["data_mes"].dt.month

        current_year = int(df["year"].max())
        prior_year = current_year - 1

        current_ytd = df[(df["year"] == current_year)]["faturamento"].sum()
        prior_ytd = df[(df["year"] == prior_year)]["faturamento"].sum()

        if prior_ytd == 0:
            return 0.0
        return float((current_ytd - prior_ytd) / prior_ytd)

    # ── Working Capital KPIs ──────────────────────────────────────────

    def contas_receber_saldo(self) -> float:
        """Total open + overdue AR balance."""
        if self._ar.empty or "status" not in self._ar.columns:
            return 0.0
        open_ar = self._ar[self._ar["status"].isin(["Aberto", "Atrasado"])]
        return float(open_ar["valor"].sum())

    def contas_pagar_saldo(self) -> float:
        """Total open AP balance."""
        if self._ap.empty or "status" not in self._ap.columns:
            return 0.0
        open_ap = self._ap[self._ap["status"] == "Aberto"]
        return float(open_ap["valor"].sum())

    def estoque_total(self) -> float:
        """Total inventory value (latest month, all categories)."""
        if self._estoque.empty:
            return 0.0

        latest_date = self._estoque["data_mes"].max()
        latest = self._estoque[self._estoque["data_mes"] == latest_date]
        return float(latest["valor_estoque"].sum())

    def ncg(self) -> float:
        """Net Working Capital Requirement = AR + Inventory - AP."""
        return self.contas_receber_saldo() + self.estoque_total() - self.contas_pagar_saldo()

    def prazo_medio_recebimento(self) -> float:
        """Average collection period (days)."""
        if self._ar.empty or "data_vencimento" not in self._ar.columns:
            return 0.0

        ar = self._ar.copy()
        if "data_emissao" not in ar.columns:
            return 0.0

        ar["prazo"] = (ar["data_vencimento"] - ar["data_emissao"]).dt.days
        valid = ar[ar["prazo"].between(0, 365)]
        if valid.empty:
            return 0.0
        return float(valid["prazo"].mean())

    def prazo_medio_estoque(self) -> float:
        """Average inventory holding period (days) using COGS."""
        if self._custo.empty or self._estoque.empty:
            return 0.0

        # Annual COGS
        custo_anual = float(self._custo["custo_mes"].sum())
        if custo_anual == 0:
            return 0.0

        # Average inventory
        estoque_medio = float(
            self._estoque.groupby("data_mes")["valor_estoque"].sum().mean()
        )

        # PME = (Average Inventory / Annual COGS) * 365
        return round((estoque_medio / custo_anual) * 365, 1)

    def prazo_medio_pagamento(self) -> float:
        """Average payment period (days)."""
        if self._ap.empty or "data_vencimento" not in self._ap.columns:
            return 0.0

        ap = self._ap.copy()
        if "data_emissao" not in ap.columns:
            return 0.0

        ap["prazo"] = (ap["data_vencimento"] - ap["data_emissao"]).dt.days
        valid = ap[ap["prazo"].between(0, 365)]
        if valid.empty:
            return 0.0
        return float(valid["prazo"].mean())

    def ciclo_financeiro(self) -> float:
        """Financial cycle = PMR + PME - PMP."""
        return round(
            self.prazo_medio_recebimento()
            + self.prazo_medio_estoque()
            - self.prazo_medio_pagamento(),
            1,
        )

    # ── Debt KPIs ─────────────────────────────────────────────────────

    def divida_total(self) -> float:
        """Total outstanding debt (latest month)."""
        if self._divida.empty:
            return 0.0

        latest_date = self._divida["data_mes"].max()
        latest = self._divida[self._divida["data_mes"] == latest_date]
        return float(latest["saldo_devedor"].sum())

    def divida_por_tipo(self) -> dict[str, float]:
        """Debt breakdown by type (latest month)."""
        if self._divida.empty:
            return {}

        latest_date = self._divida["data_mes"].max()
        latest = self._divida[self._divida["data_mes"] == latest_date]
        result: dict[str, float] = {}
        for _, row in latest.iterrows():
            tipo = str(row["tipo_divida"])
            result[tipo] = result.get(tipo, 0.0) + float(row["saldo_devedor"])
        return result

    def juros_mensais(self) -> float:
        """Total monthly interest payments (latest month)."""
        if self._divida.empty:
            return 0.0

        latest_date = self._divida["data_mes"].max()
        latest = self._divida[self._divida["data_mes"] == latest_date]
        return float(latest["juros_mes"].sum())

    def divida_receita_anualizada(self) -> float:
        """Debt / Annualized Revenue ratio."""
        total_debt = self.divida_total()
        if total_debt == 0:
            return 0.0

        anualizada = self.receita_ultimos_12m()
        if anualizada == 0:
            return 0.0

        return round(total_debt / anualizada, 4)

    def cobertura_juros(self) -> float:
        """Interest coverage ratio (estimated EBITDA / interest)."""
        juros = self.juros_mensais() * 12  # annualized
        if juros == 0:
            return float("inf")

        # Estimate EBITDA: 15% of annualized revenue (simple proxy)
        receita = self.receita_ultimos_12m()
        ebitda = receita * 0.15

        return round(ebitda / juros, 2)

    # ── Cash KPIs ─────────────────────────────────────────────────────

    def saldo_final_projetado(self) -> float:
        """Projected ending cash balance."""
        if self._cashflow.empty:
            return 0.0
        return float(self._cashflow["saldo_final_dia"].iloc[-1])

    def menor_saldo_projetado(self) -> float:
        """Lowest projected cash balance."""
        if self._cashflow.empty:
            return 0.0
        return float(self._cashflow["saldo_final_dia"].min())

    def dias_caixa_negativo(self) -> int:
        """Number of days with negative cash balance."""
        if self._cashflow.empty:
            return 0
        return int((self._cashflow["saldo_final_dia"] < 0).sum())

    def necessidade_maxima_caixa(self) -> float:
        """Maximum cash need (absolute value of most negative balance)."""
        if self._cashflow.empty:
            return 0.0
        min_balance = self._cashflow["saldo_final_dia"].min()
        return abs(min(min_balance, 0.0))
