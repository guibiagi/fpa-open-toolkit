"""Tests for :mod:`forecasting.revenue_forecast`."""

from __future__ import annotations

import pandas as pd
import pytest

from forecasting.revenue_forecast import RevenueForecast, forecast


# ── helpers ────────────────────────────────────────────────────────────────


def _make_flat_history(months: int = 48, value: float = 4_000_000.0) -> pd.DataFrame:
    """Create flat (no seasonality, no trend) historical data."""
    import datetime

    rows = []
    start = datetime.date(2022, 1, 1)
    for i in range(months):
        year = start.year + (start.month - 1 + i) // 12
        month = (start.month - 1 + i) % 12 + 1
        day = min(start.day, 28)
        rows.append({"data_mes": datetime.date(year, month, day), "faturamento": value})
    return pd.DataFrame(rows)


def _load_real_data() -> pd.DataFrame:
    """Load the synthetic faturamento_historico for integration tests."""
    from data_generation.synthetic_generator import generate_all

    return generate_all(42)["faturamento_historico"]


# ── unit tests ─────────────────────────────────────────────────────────────


class TestConstructor:
    """RevenueForecast initialization."""

    def test_aggregates_monthly(self) -> None:
        """Multiple rows per month are aggregated to monthly totals."""
        import datetime

        rows = [
            {"data_mes": datetime.date(2024, 1, 1), "faturamento": 100.0},
            {"data_mes": datetime.date(2024, 1, 1), "faturamento": 200.0},
            {"data_mes": datetime.date(2024, 2, 1), "faturamento": 300.0},
        ]
        df = pd.DataFrame(rows)
        engine = RevenueForecast(df)
        hist = engine.historico()
        assert len(hist) == 2
        assert hist["faturamento"].iloc[0] == 300.0  # 100 + 200
        assert hist["faturamento"].iloc[1] == 300.0

    def test_insufficient_data_raises(self) -> None:
        """Need at least 3 months of data."""
        import datetime

        df = pd.DataFrame(
            [
                {"data_mes": datetime.date(2024, 1, 1), "faturamento": 100.0},
                {"data_mes": datetime.date(2024, 2, 1), "faturamento": 100.0},
            ]
        )
        engine = RevenueForecast(df)
        with pytest.raises(ValueError, match="at least 3 months"):
            engine.forecast()


class TestForecastOutput:
    """Forecast output structure and ranges."""

    def test_output_columns(self) -> None:
        df = _load_real_data()
        engine = RevenueForecast(df)
        proj = engine.forecast(12)

        expected = {"data_mes", "forecast_base", "forecast_otimista", "forecast_pessimista"}
        assert set(proj.columns) == expected

    def test_horizon_length(self) -> None:
        df = _load_real_data()
        engine = RevenueForecast(df)

        for h in [1, 6, 12, 24]:
            proj = engine.forecast(h)
            assert len(proj) == h, f"horizon={h} → {len(proj)} rows"

    def test_horizon_clamped(self) -> None:
        df = _load_real_data()
        engine = RevenueForecast(df)

        assert len(engine.forecast(0)) == 1  # clamped to 1
        assert len(engine.forecast(50)) == 24  # clamped to 24

    def test_forecast_starts_after_history(self) -> None:
        df = _load_real_data()
        engine = RevenueForecast(df)
        proj = engine.forecast(12)

        last_hist = engine.historico()["data_mes"].max()
        first_proj = proj["data_mes"].min()
        assert first_proj > last_hist, f"{first_proj} not > {last_hist}"

    def test_values_never_negative(self) -> None:
        df = _load_real_data()
        engine = RevenueForecast(df)
        proj = engine.forecast(12)

        for col in ["forecast_base", "forecast_otimista", "forecast_pessimista"]:
            assert (proj[col] >= 0).all(), f"{col} has negative values"


class TestScenarios:
    """Scenario ordering."""

    def test_optimistic_greater_than_base(self) -> None:
        df = _load_real_data()
        engine = RevenueForecast(df)
        proj = engine.forecast(12)

        assert (proj["forecast_otimista"] > proj["forecast_base"]).all()

    def test_pessimistic_less_than_base(self) -> None:
        df = _load_real_data()
        engine = RevenueForecast(df)
        proj = engine.forecast(12)

        assert (proj["forecast_pessimista"] < proj["forecast_base"]).all()

    def test_scenario_ratio(self) -> None:
        """Optimista should be ~10% above base, Pessimista ~10% below."""
        df = _load_real_data()
        engine = RevenueForecast(df)
        proj = engine.forecast(12)

        ratio_ot = proj["forecast_otimista"] / proj["forecast_base"]
        ratio_pe = proj["forecast_pessimista"] / proj["forecast_base"]

        # Allow small floating-point drift from iterated multiplication
        assert ratio_ot.min() >= 1.09  # ~10%
        assert ratio_pe.max() <= 0.91


class TestSeasonality:
    """Seasonal patterns in forecasts."""

    def test_december_peak(self) -> None:
        """December should have the highest seasonal index for realistic data."""
        df = _load_real_data()
        engine = RevenueForecast(df)
        proj = engine.forecast(24)  # Need at least 2 Decembers

        dec_rows = proj[pd.to_datetime(proj["data_mes"]).dt.month == 12]
        other_rows = proj[pd.to_datetime(proj["data_mes"]).dt.month != 12]

        if len(dec_rows) > 0 and len(other_rows) > 0:
            dec_avg = dec_rows["forecast_base"].mean()
            other_avg = other_rows["forecast_base"].mean()
            assert dec_avg > other_avg, f"Dec {dec_avg:,.0f} ≤ other {other_avg:,.0f}"

    def test_flat_data_no_seasonal_amplification(self) -> None:
        """Flat historical data should produce flat forecasts."""
        df = _make_flat_history(48, 4_000_000)
        engine = RevenueForecast(df)
        proj = engine.forecast(12)

        # Values should stay close to 4M (within ±5% due to slight growth rounding)
        base = proj["forecast_base"]
        assert base.min() >= 3_800_000, f"Min {base.min():,.0f} too low"
        assert base.max() <= 4_200_000, f"Max {base.max():,.0f} too high"


class TestConvenienceFunction:
    """The ``forecast()`` convenience function."""

    def test_returns_dataframe(self) -> None:
        df = _load_real_data()
        result = forecast(df, horizon=6)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 6

    def test_writes_csv(self, tmp_path) -> None:
        import os

        df = _load_real_data()
        out = tmp_path / "forecast_test.csv"
        forecast(df, horizon=6, output_path=str(out))

        assert os.path.exists(str(out))
        written = pd.read_csv(str(out))
        assert len(written) == 6
