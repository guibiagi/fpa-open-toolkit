"""Formatting utilities for Brazilian locale (BRL, percentage).

All functions are pure — no external dependencies other than
the Python standard library.
"""

from __future__ import annotations

from typing import Union


def format_brl(value: Union[float, int]) -> str:
    """Format a numeric value as Brazilian Real (BRL).

    Uses Brazilian locale conventions:
    - Thousands separator: ``.``
    - Decimal separator: ``,``
    - Always 2 decimal places

    Examples
    --------
    >>> format_brl(1234567.89)
    '1.234.567,89'
    >>> format_brl(1000)
    '1.000,00'
    >>> format_brl(0)
    '0,00'
    >>> format_brl(-500.5)
    '-500,50'
    """
    if value is None:
        return "0,00"

    # Handle negative sign
    sign = "-" if value < 0 else ""
    value = abs(float(value))

    # Split integer and decimal parts
    integer_part = int(value)
    decimal_part = int(round((value - integer_part) * 100))

    # Format integer part with Brazilian thousands separator
    int_str = f"{integer_part:,}".replace(",", ".")

    return f"{sign}{int_str},{decimal_part:02d}"


def format_pct(value: Union[float, int]) -> str:
    """Format a numeric value as a Brazilian percentage string.

    The input is expected as a decimal fraction (e.g. ``0.125`` for 12.5%).

    Rules:
    - One decimal place
    - Brazilian decimal separator (``,``)
    - Trailing ``%``
    - Handles ``None``, negative, and zero

    Examples
    --------
    >>> format_pct(0.125)
    '12,5%'
    >>> format_pct(1.0)
    '100,0%'
    >>> format_pct(0)
    '0,0%'
    >>> format_pct(-0.05)
    '-5,0%'
    >>> format_pct(None)
    '0,0%'
    """
    if value is None:
        return "0,0%"

    percentage = float(value) * 100
    sign = "-" if percentage < 0 else ""
    percentage = abs(percentage)

    int_part = int(percentage)
    dec_part = int(round((percentage - int_part) * 10))

    return f"{sign}{int_part},{dec_part}%"
