"""Cash flow projection engine — 90-day daily projection with BR business days.

Implements spec v1.1 §7.3:
- Daily projection using Brazilian business days (no weekends/holidays)
- Entries: open receivables + forecast distributed over business days
- Exits: open payables on their due dates
- Weighted distribution: Tue/Wed/Thu heavier
- Starting balance parameter
- Risk classification per day

Usage::

    from cashflow.cashflow_projection import CashflowProjection

    engine = CashflowProjection(
        contas_receber=ar_df,
        contas_pagar=ap_df,
        forecast=forecast_df,
        saldo_inicial=500_000.0,
    )
    proj = engine.project(horizon=90)
    proj.to_csv("data/outputs/fluxo_caixa_projetado.csv", index=False)
"""

from __future__ import annotations

import datetime
from typing import Optional

import pandas as pd

from utils.dates import is_business_day, next_business_day


class CashflowProjection:
    """90-day cash flow projection engine.

    Parameters
    ----------
    contas_receber:
        Accounts receivable DataFrame from synthetic generator.
    contas_pagar:
        Accounts payable DataFrame from synthetic generator.
    forecast:
        Revenue forecast DataFrame from the revenue forecast engine.
    saldo_inicial:
        Starting cash balance in BRL (default: 0).
    """

    # ── Configuration constants ──────────────────────────────────────

    # Day-of-week weights for distributing monthly forecast
    # Tuesday, Wednesday, Thursday get higher weights
    DAY_WEIGHTS = {
        0: 0.08,   # Monday
        1: 0.22,   # Tuesday
        2: 0.24,   # Wednesday
        3: 0.22,   # Thursday
        4: 0.16,   # Friday
        5: 0.04,   # Saturday (rarely a business day, but safe)
        6: 0.04,   # Sunday
    }

    # Risk thresholds
    LOW_BALANCE_WARNING_RATIO = 0.15  # < 15% of monthly revenue → warning
    NEGATIVE_BALANCE_THRESHOLD = 0.0

    def __init__(
        self,
        contas_receber: pd.DataFrame,
        contas_pagar: pd.DataFrame,
        forecast: pd.DataFrame | None = None,
        saldo_inicial: float = 0.0,
    ) -> None:
        self._ar = contas_receber.copy() if contas_receber is not None else pd.DataFrame()
        self._ap = contas_pagar.copy() if contas_pagar is not None else pd.DataFrame()
        self._forecast = forecast.copy() if forecast is not None else pd.DataFrame()
        self._saldo_inicial = float(saldo_inicial)

        # Normalize date columns
        for col in ["data_emissao", "data_vencimento", "data_pagamento"]:
            if col in self._ar.columns:
                self._ar[col] = pd.to_datetime(self._ar[col])
            if col in self._ap.columns:
                self._ap[col] = pd.to_datetime(self._ap[col])

        # Pre-compute monthly revenue for risk thresholds
        self._monthly_revenue = self._compute_monthly_revenue()

    # ── public ───────────────────────────────────────────────────────

    def project(self, horizon: int = 90) -> pd.DataFrame:
        """Generate daily cash flow projection.

        Parameters
        ----------
        horizon:
            Number of calendar days to project (default: 90, min: 30, max: 180).

        Returns
        -------
        pd.DataFrame
            Columns: ``data``, ``entradas_previstas``, ``saidas_previstas``,
            ``saldo_inicial_dia``, ``saldo_final_dia``, ``observacao``.
        """
        horizon = max(30, min(horizon, 180))

        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=horizon)

        # Build all projection days
        days = self._build_projection_days(today, end_date)

        # Calculate entries (receivables + forecast distribution)
        entries = self._calculate_entries(days, today, end_date)

        # Calculate exits (payables)
        exits = self._calculate_exits(days, today, end_date)

        # Build daily balance
        result = self._build_daily_balance(days, entries, exits)

        return result

    # ── internal: day generation ─────────────────────────────────────

    def _build_projection_days(
        self,
        start: datetime.date,
        end: datetime.date,
    ) -> pd.DataFrame:
        """Generate all calendar days in the projection window."""
        dates = pd.date_range(start=start, end=end, freq="D")
        return pd.DataFrame({"data": dates})

    # ── internal: entries ────────────────────────────────────────────

    def _calculate_entries(
        self,
        days: pd.DataFrame,
        today: datetime.date,
        end_date: datetime.date,
    ) -> pd.Series:
        """Calculate total daily cash inflows."""
        entries = pd.Series(0.0, index=days.index)

        # 1. Open receivables falling due in the window
        if self._ar.empty or "status" not in self._ar.columns:
            pass
        else:
            open_ar = self._ar[
                (self._ar["status"] == "Aberto")
                | (self._ar["status"] == "Atrasado")
            ].copy()

            for _, title in open_ar.iterrows():
                due = title["data_vencimento"]
                due_date = due.date() if hasattr(due, "date") else due
                biz_due = next_business_day(due_date)

                # Past-due titles: spread across first 5 business days
                if biz_due < today:
                    offset = abs(hash(str(title.get("id_titulo", "")))) % 5
                    d = today
                    c = 0
                    while True:
                        if is_business_day(d):
                            if c == offset:
                                biz_due = d
                                break
                            c += 1
                        d += datetime.timedelta(days=1)

                if today <= biz_due <= end_date:
                    mask = days["data"].dt.date == biz_due
                    if mask.any():
                        idx = mask.idxmax()
                        entries[idx] = entries.get(idx, 0.0) + float(title["valor"])

        # 2. Forecast distribution over business days
        entries = self._distribute_forecast(days, entries, today, end_date)

        return entries

    def _distribute_forecast(
        self,
        days: pd.DataFrame,
        entries: pd.Series,
        today: datetime.date,
        end_date: datetime.date,
    ) -> pd.Series:
        """Distribute monthly forecast across business days with weights."""
        if self._forecast.empty:
            return entries

        for _, row in self._forecast.iterrows():
            forecast_month = pd.Timestamp(row["data_mes"]).date()
            base = float(row.get("forecast_base", 0.0))

            if base <= 0:
                continue

            # Get all business days in this month within the window
            month_start = max(
                today,
                forecast_month.replace(day=1),
            )
            # Last day of forecast month
            if forecast_month.month == 12:
                month_end = datetime.date(forecast_month.year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                month_end = datetime.date(forecast_month.year, forecast_month.month + 1, 1) - datetime.timedelta(days=1)

            month_end = min(month_end, end_date)

            if month_start > month_end:
                continue

            # Collect business days in this range
            biz_days: list[tuple[int, datetime.date]] = []
            d = month_start
            while d <= month_end:
                if is_business_day(d):
                    biz_days.append((d.weekday(), d))
                d += datetime.timedelta(days=1)

            if not biz_days:
                continue

            # Calculate weights
            weights = [self.DAY_WEIGHTS.get(wd, 0.10) for wd, _ in biz_days]
            total_weight = sum(weights)
            if total_weight == 0:
                continue

            # Distribute
            for (_, biz_date), weight in zip(biz_days, weights):
                fraction = weight / total_weight
                value = base * fraction

                mask = days["data"].dt.date == biz_date
                if mask.any():
                    idx = mask.idxmax()
                    entries[idx] = entries.get(idx, 0.0) + value

        return entries

    # ── internal: exits ──────────────────────────────────────────────

    def _calculate_exits(
        self,
        days: pd.DataFrame,
        today: datetime.date,
        end_date: datetime.date,
    ) -> pd.Series:
        """Calculate total daily cash outflows."""
        exits = pd.Series(0.0, index=days.index)

        if self._ap.empty or "status" not in self._ap.columns:
            return exits

        open_ap = self._ap[
            self._ap["status"] == "Aberto"
        ].copy()

        for _, title in open_ap.iterrows():
            due = title["data_vencimento"]
            due_date = due.date() if hasattr(due, "date") else due
            biz_due = next_business_day(due_date)

            # Past-due titles: spread across first 5 business days
            if biz_due < today:
                offset = abs(hash(str(title.get("id_titulo", "")))) % 5
                d = today
                c = 0
                while True:
                    if is_business_day(d):
                        if c == offset:
                            biz_due = d
                            break
                        c += 1
                    d += datetime.timedelta(days=1)

            if today <= biz_due <= end_date:
                mask = days["data"].dt.date == biz_due
                if mask.any():
                    idx = mask.idxmax()
                    exits[idx] = exits.get(idx, 0.0) + float(title["valor"])

        return exits

    # ── internal: daily balance ──────────────────────────────────────

    def _build_daily_balance(
        self,
        days: pd.DataFrame,
        entries: pd.Series,
        exits: pd.Series,
    ) -> pd.DataFrame:
        """Build the final daily balance DataFrame."""
        rows = []
        carry = self._saldo_inicial

        for i in range(len(days)):
            date = days["data"].iloc[i]
            entrada = round(float(entries.get(i, 0.0)), 2)
            saida = round(float(exits.get(i, 0.0)), 2)

            saldo_inicial_dia = round(carry, 2)
            saldo_final_dia = round(saldo_inicial_dia + entrada - saida, 2)

            observacao = self._classify_day(saldo_final_dia)

            rows.append(
                {
                    "data": date.date().isoformat(),
                    "entradas_previstas": entrada,
                    "saidas_previstas": saida,
                    "saldo_inicial_dia": saldo_inicial_dia,
                    "saldo_final_dia": saldo_final_dia,
                    "observacao": observacao,
                }
            )

            carry = saldo_final_dia

        result = pd.DataFrame(rows)
        result["data"] = pd.to_datetime(result["data"])
        return result

    def _classify_day(self, saldo: float) -> str:
        """Classify the risk level for a day's closing balance."""
        if saldo < self.NEGATIVE_BALANCE_THRESHOLD:
            return "Risco: caixa negativo"
        elif self._monthly_revenue > 0 and saldo < self._monthly_revenue * self.LOW_BALANCE_WARNING_RATIO:
            return "Atenção: saldo baixo"
        else:
            return "Caixa normal"

    # ── internal: utilities ──────────────────────────────────────────

    def _compute_monthly_revenue(self) -> float:
        """Estimate average monthly revenue for risk thresholds."""
        if not self._forecast.empty and "forecast_base" in self._forecast.columns:
            return float(self._forecast["forecast_base"].mean())

        # Fallback: use open receivables
        if not self._ar.empty:
            open_ar = self._ar[self._ar["status"].isin(["Aberto", "Atrasado"])]
            if not open_ar.empty:
                return float(open_ar["valor"].sum() / 3)  # rough estimate

        return 1_000_000.0  # safe default

    # ── convenience properties ───────────────────────────────────────

    def menor_saldo(self, projection: Optional[pd.DataFrame] = None) -> float:
        """Return the lowest projected balance."""
        if projection is None:
            projection = self.project()
        return float(projection["saldo_final_dia"].min())

    def dias_negativos(self, projection: Optional[pd.DataFrame] = None) -> int:
        """Count days with negative balance."""
        if projection is None:
            projection = self.project()
        return int((projection["saldo_final_dia"] < 0).sum())

    def necessidade_maxima_caixa(self, projection: Optional[pd.DataFrame] = None) -> float:
        """Maximum cash needed (most negative cumulative balance)."""
        if projection is None:
            projection = self.project()
        min_balance = projection["saldo_final_dia"].min()
        return abs(min(min_balance, 0.0))
