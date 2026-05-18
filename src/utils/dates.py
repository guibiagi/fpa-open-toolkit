"""Brazilian business days and holidays utilities.

Provides functions to work with Brazilian business days,
accounting for national holidays via the ``holidays`` library.

Usage::

    >>> from utils.dates import is_business_day, add_business_days
    >>> from datetime import date
    >>> is_business_day(date(2024, 1, 1))  # Confraternização Universal
    False
"""

from __future__ import annotations

import datetime
from typing import List

import holidays

# Singleton holidays instance — ``__contains__`` works in holidays>=0.96
# even though iteration may not enumerate upcoming years.
_BRAZIL_HOLIDAYS = holidays.Brazil(subdiv=None)


def is_business_day(date: datetime.date) -> bool:
    """Check if *date* is a Brazilian business day.

    Returns ``True`` when *date* is a weekday (Mon-Fri) and **not**
    a Brazilian national holiday.
    """
    if date.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return date not in _BRAZIL_HOLIDAYS


def next_business_day(date: datetime.date) -> datetime.date:
    """Return the next Brazilian business day after or equal to *date*.

    If *date* itself is a business day, returns it unchanged.
    Otherwise advances day-by-day until a business day is found.
    """
    while not is_business_day(date):
        date += datetime.timedelta(days=1)
    return date


def business_days_in_month(year: int, month: int) -> List[datetime.date]:
    """Return all Brazilian business days in ``(year, month)``.

    The list is sorted chronologically.
    """
    result: List[datetime.date] = []
    current = datetime.date(year, month, 1)
    # Advance to next month to know when to stop
    if month == 12:
        end = datetime.date(year + 1, 1, 1)
    else:
        end = datetime.date(year, month + 1, 1)

    while current < end:
        if is_business_day(current):
            result.append(current)
        current += datetime.timedelta(days=1)
    return result


def add_business_days(date: datetime.date, n: int) -> datetime.date:
    """Add *n* business days to *date* and return the resulting date.

    *n* can be negative (go backward).  ``n=0`` returns the next
    business day (or *date* itself if it already is one).
    """
    if n >= 0:
        result = next_business_day(date)
        count = 0
        while count < n:
            result += datetime.timedelta(days=1)
            if is_business_day(result):
                count += 1
        return result
    else:
        # Negative: go backwards
        result = date
        count = 0
        while count < abs(n):
            result -= datetime.timedelta(days=1)
            if is_business_day(result):
                count += 1
        return result
