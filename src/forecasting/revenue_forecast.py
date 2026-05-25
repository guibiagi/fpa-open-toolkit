"""Revenue forecast engine — moving average + trend + seasonality.

Implements the MVP model from spec v1.1 §7.2:
- 3-month moving average
- 12-month average growth rate
- Seasonal index per calendar month
- 3 scenarios: base, otimista (+10%), pessimista (-10%)

Usage::

    from forecasting.revenue_forecast import RevenueForecast, forecast

    engine = RevenueForecast(faturamento_df)
    hist = engine.historico()        # aggregated monthly history
    proj = engine.forecast(horizon=12)  # 12-month forecast
    proj.to_csv("data/outputs/forecast_faturamento.csv", index=False)

    # Or use the convenience function:
    result = forecast(faturamento_df, horizon=12)
"""

from __future__ import annotations

import datetime
from typing import Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Public API — convenience function
# ---------------------------------------------------------------------------


def forecast(
    faturamento_df: pd.DataFrame,
    horizon: int = 12,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """Run the full forecast pipeline and return the projection DataFrame.

    Parameters
    ----------
    faturamento_df:
        Historical revenue DataFrame. Must contain columns
        ``data_mes`` and ``faturamento``.
    horizon:
        Number of months to forecast (default: 12, max: 24).
    output_path:
        If provided, write the forecast CSV to this path.

    Returns
    -------
    pd.DataFrame
        Columns: ``data_mes``, ``forecast_base``, ``forecast_otimista``,
        ``forecast_pessimista``.
    """
    engine = RevenueForecast(faturamento_df)
    result = engine.forecast(horizon=horizon)

    if output_path:
        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False)

    return result


# ---------------------------------------------------------------------------
# RevenueForecast class
# ---------------------------------------------------------------------------


class RevenueForecast:
    """Revenue forecast engine for FP&A Open Toolkit.

    Parameters
    ----------
    faturamento_df:
        Raw historical revenue DataFrame from the synthetic generator.
        Must contain ``data_mes`` and ``faturamento`` columns.
        Multiple rows per month (family × channel) are aggregated.
    """

    def __init__(self, faturamento_df: pd.DataFrame) -> None:
        # Aggregate to monthly totals
        self._monthly = (
            faturamento_df.groupby("data_mes")["faturamento"]
            .sum()
            .reset_index()
            .sort_values("data_mes")
            .reset_index(drop=True)
        )
        self._monthly["data_mes"] = pd.to_datetime(self._monthly["data_mes"])

        # Pre-compute seasonality indices
        self._seasonal_idx = self._compute_seasonality()

    # ── public methods ─────────────────────────────────────────────────

    def historico(self) -> pd.DataFrame:
        """Return the aggregated monthly history used for forecasting."""
        return self._monthly.copy()

    def forecast(self, horizon: int = 12) -> pd.DataFrame:
        """Generate revenue forecast for *horizon* months ahead.

        Parameters
        ----------
        horizon:
            Number of months to project (1–24, clamped).

        Returns
        -------
        pd.DataFrame
            Columns: ``data_mes``, ``forecast_base``, ``forecast_otimista``,
            ``forecast_pessimista``.
            Values are never negative.
        """
        horizon = max(1, min(horizon, 24))

        last_month = self._monthly["data_mes"].max()
        values = self._monthly["faturamento"].values

        if len(values) < 3:
            raise ValueError(
                "Need at least 3 months of historical data to forecast"
            )

        # Moving average of last 3 months
        ma3 = float(np.mean(values[-3:]))

        # Average growth rate over last 12 months
        growth_rate = self._monthly_growth_rate()

        # Build forecast month by month
        rows = []
        carry = ma3  # starting point for the forecast

        for i in range(1, horizon + 1):
            month_date = self._add_months(last_month, i)
            month_num = month_date.month

            # Apply trend + seasonality
            seasonal_factor = self._seasonal_idx.get(month_num, 1.0)
            base = carry * (1 + growth_rate) * seasonal_factor

            # Add small noise for realism but keep deterministic
            # (no noise in MVP — pure formula)

            # Ensure never negative
            base = max(base, 0.0)

            otimista = base * 1.10
            pessimista = base * 0.90

            rows.append(
                {
                    "data_mes": month_date,
                    "forecast_base": round(base, 2),
                    "forecast_otimista": round(otimista, 2),
                    "forecast_pessimista": round(pessimista, 2),
                }
            )

            # New carry = new base for next iteration's trend
            carry = base

        result = pd.DataFrame(rows)
        result["data_mes"] = pd.to_datetime(result["data_mes"])
        return result

    # ── internal ───────────────────────────────────────────────────────

    def _compute_seasonality(self) -> dict[int, float]:
        """Compute seasonal index per calendar month.

        Index = average revenue for that month / overall monthly average.
        Returns a dict of {month_number: index}.
        """
        df = self._monthly.copy()
        df["month"] = df["data_mes"].dt.month
        df["year"] = df["data_mes"].dt.year

        overall_avg = df["faturamento"].mean()
        if overall_avg == 0:
            return {m: 1.0 for m in range(1, 13)}

        seasonal: dict[int, float] = {}
        for m in range(1, 13):
            month_data = df[df["month"] == m]["faturamento"]
            if len(month_data) > 0 and overall_avg > 0:
                seasonal[m] = month_data.mean() / overall_avg
            else:
                seasonal[m] = 1.0

        # Normalize so average of all indices = 1.0
        avg_idx = sum(seasonal.values()) / 12
        if avg_idx > 0:
            seasonal = {k: v / avg_idx for k, v in seasonal.items()}

        return seasonal

    def _monthly_growth_rate(self) -> float:
        """Average monthly growth rate over available history.

        Uses CAGR formula: (last / first) ^ (1 / n) - 1, then
        divides by ~months between observations.

        For better stability, uses the last 12 months when possible.
        """
        values = self._monthly["faturamento"].values
        n = min(len(values), 12)
        recent = values[-n:]

        if len(recent) < 2:
            return 0.0

        # Simple: (last - first) / first / months
        first = recent[0]
        last = recent[-1]
        if first <= 0:
            return 0.0

        return (last / first) ** (1.0 / (n - 1)) - 1.0

    @staticmethod
    def _add_months(dt: pd.Timestamp, n: int) -> pd.Timestamp:
        """Add n months to a Timestamp."""
        month = dt.month - 1 + n
        year = dt.year + month // 12
        month = month % 12 + 1
        day = min(dt.day, 28)  # safe day
        return pd.Timestamp(datetime.date(year, month, day))
