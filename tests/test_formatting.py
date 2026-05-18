"""Tests for src.utils.formatting — BRL and percentage formatting."""

from __future__ import annotations

import pytest

from utils.formatting import format_brl, format_pct


class TestFormatBRL:
    """Tests for :func:`format_brl`."""

    def test_large_number(self):
        """1,234,567.89 should become '1.234.567,89'."""
        assert format_brl(1234567.89) == "1.234.567,89"

    def test_thousand(self):
        """1000 should become '1.000,00'."""
        assert format_brl(1000) == "1.000,00"

    def test_zero(self):
        """0 should become '0,00'."""
        assert format_brl(0) == "0,00"

    def test_negative(self):
        """-500.50 should become '-500,50'."""
        assert format_brl(-500.5) == "-500,50"

    def test_integer_input(self):
        """Integer 42 should become '42,00'."""
        assert format_brl(42) == "42,00"

    def test_small_decimal(self):
        """0.99 should become '0,99'."""
        assert format_brl(0.99) == "0,99"

    def test_rounding(self):
        """1.999 should become '1.999,00'."""
        assert format_brl(1999) == "1.999,00"

    def test_none_returns_zero(self):
        """None should return '0,00'."""
        assert format_brl(None) == "0,00"  # type: ignore[arg-type]


class TestFormatPct:
    """Tests for :func:`format_pct`."""

    def test_decimal_fraction(self):
        """0.125 should become '12,5%'."""
        assert format_pct(0.125) == "12,5%"

    def test_one_hundred_percent(self):
        """1.0 should become '100,0%'."""
        assert format_pct(1.0) == "100,0%"

    def test_zero_percent(self):
        """0 should become '0,0%'."""
        assert format_pct(0) == "0,0%"

    def test_negative(self):
        """-0.05 should become '-5,0%'."""
        assert format_pct(-0.05) == "-5,0%"

    def test_small_value(self):
        """0.003 should become '0,3%'."""
        assert format_pct(0.003) == "0,3%"

    def test_even_percentage(self):
        """0.50 should become '50,0%'."""
        assert format_pct(0.50) == "50,0%"

    def test_none_returns_zero(self):
        """None should return '0,0%'."""
        assert format_pct(None) == "0,0%"  # type: ignore[arg-type]
