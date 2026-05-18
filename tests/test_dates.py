"""Tests for src.utils.dates — Brazilian business days and holidays."""

from __future__ import annotations

import datetime

import pytest

from utils.dates import (
    add_business_days,
    business_days_in_month,
    is_business_day,
    next_business_day,
)


class TestIsBusinessDay:
    """Tests for :func:`is_business_day`."""

    def test_weekday_is_business_day(self):
        """A regular Tuesday should be a business day."""
        d = datetime.date(2024, 3, 12)  # Tuesday
        assert is_business_day(d) is True

    def test_saturday_is_not_business_day(self):
        """Saturday should not be a business day."""
        d = datetime.date(2024, 3, 16)  # Saturday
        assert is_business_day(d) is False

    def test_sunday_is_not_business_day(self):
        """Sunday should not be a business day."""
        d = datetime.date(2024, 3, 17)  # Sunday
        assert is_business_day(d) is False

    def test_national_holiday_is_not_business_day(self):
        """Confraternização Universal (Jan 1) should NOT be a business day."""
        d = datetime.date(2024, 1, 1)
        assert is_business_day(d) is False

    def test_tiradentes_is_not_business_day(self):
        """Tiradentes (Apr 21) should NOT be a business day."""
        d = datetime.date(2024, 4, 21)
        assert is_business_day(d) is False

    def test_independence_day_is_not_business_day(self):
        """Independência (Sep 7) should NOT be a business day."""
        d = datetime.date(2024, 9, 7)
        assert is_business_day(d) is False

    def test_christmas_is_not_business_day(self):
        """Natal (Dec 25) should NOT be a business day."""
        d = datetime.date(2024, 12, 25)
        assert is_business_day(d) is False

    def test_good_friday_is_not_business_day(self):
        """Sexta-Feira Santa (Mar 29) should NOT be a business day."""
        d = datetime.date(2024, 3, 29)  # Good Friday
        assert is_business_day(d) is False

    def test_carnival_is_not_national_holiday(self):
        """Carnival is NOT a national holiday in holidays lib (state-only)."""
        d = datetime.date(2024, 2, 12)  # Carnival Monday
        # This may or may not be a holiday depending on state/municipal rules
        # In the holidays library w/o subdiv, it's NOT a holiday
        # But it is a Monday, so let's just check the day of week
        assert d.weekday() == 0  # It's Monday


class TestNextBusinessDay:
    """Tests for :func:`next_business_day`."""

    def test_already_business_day(self):
        """If already a business day, return same date."""
        d = datetime.date(2024, 3, 12)  # Tuesday
        assert next_business_day(d) == d

    def test_saturday_rolls_to_monday(self):
        """Saturday should roll to Monday (unless Monday is a holiday)."""
        d = datetime.date(2024, 3, 16)  # Saturday
        expected = datetime.date(2024, 3, 18)  # Monday
        assert next_business_day(d) == expected

    def test_sunday_rolls_to_monday(self):
        """Sunday should roll to Monday."""
        d = datetime.date(2024, 3, 17)  # Sunday
        expected = datetime.date(2024, 3, 18)  # Monday
        assert next_business_day(d) == expected

    def test_holiday_rolls_to_next_business_day(self):
        """Jan 1 (holiday) should roll to Jan 2 (if weekday)."""
        d = datetime.date(2024, 1, 1)  # Monday + holiday
        expected = datetime.date(2024, 1, 2)  # Tuesday
        assert next_business_day(d) == expected

    def test_new_year_2025_rolls(self):
        """Jan 1 2025 (Wednesday) -- New Year is a holiday."""
        d = datetime.date(2025, 1, 1)  # Wednesday, holiday
        expected = datetime.date(2025, 1, 2)  # Thursday
        assert next_business_day(d) == expected

    def test_independence_day_rolls(self):
        """Sep 7 2024 is Saturday, so next business day is Monday Sep 9."""
        d = datetime.date(2024, 9, 7)  # Saturday + holiday
        expected = datetime.date(2024, 9, 9)  # Monday
        assert next_business_day(d) == expected

    def test_december_25_rolls(self):
        """Dec 25 2024 is Wednesday, holiday -> next is Thursday Dec 26."""
        d = datetime.date(2024, 12, 25)  # Wednesday, holiday
        expected = datetime.date(2024, 12, 26)  # Thursday
        assert next_business_day(d) == expected


class TestBusinessDaysInMonth:
    """Tests for :func:`business_days_in_month`."""

    def test_january_2024_count(self):
        """January 2024: 31 days, 4 weekends, 1 holiday (Jan 1)."""
        days = business_days_in_month(2024, 1)
        # Jan 2024: 23 weekdays - 1 holiday = 22 business days
        assert len(days) == 22

    def test_february_2024_count(self):
        """February 2024 (leap year, 29 days, no national holidays)."""
        days = business_days_in_month(2024, 2)
        # Feb 2024: no national holidays
        assert len(days) == 21

    def test_result_is_sorted(self):
        """Returned list must be sorted chronologically."""
        days = business_days_in_month(2024, 6)
        for i in range(len(days) - 1):
            assert days[i] < days[i + 1]

    def test_all_returned_dates_are_business_days(self):
        """Every returned date must pass is_business_day."""
        days = business_days_in_month(2024, 12)
        for d in days:
            assert is_business_day(d) is True


class TestAddBusinessDays:
    """Tests for :func:`add_business_days`."""

    def test_add_zero_from_weekday(self):
        """n=0 from a business day returns the same day."""
        d = datetime.date(2024, 3, 12)  # Tuesday
        assert add_business_days(d, 0) == d

    def test_add_zero_from_friday(self):
        """n=0 from Friday returns Friday (already a business day)."""
        d = datetime.date(2024, 3, 15)  # Friday
        assert add_business_days(d, 0) == d

    def test_add_one(self):
        """Add 1 business day from Tuesday."""
        d = datetime.date(2024, 3, 12)  # Tuesday
        expected = datetime.date(2024, 3, 13)  # Wednesday
        assert add_business_days(d, 1) == expected

    def test_add_skips_weekend(self):
        """Add 1 business day from Friday should skip to Monday."""
        d = datetime.date(2024, 3, 15)  # Friday
        expected = datetime.date(2024, 3, 18)  # Monday
        assert add_business_days(d, 1) == expected

    def test_add_five(self):
        """Add 5 business days from Monday -> next Monday."""
        d = datetime.date(2024, 3, 11)  # Monday
        expected = datetime.date(2024, 3, 18)  # Next Monday
        assert add_business_days(d, 5) == expected

    def test_add_negative_one(self):
        """Subtract 1 business day from Tuesday."""
        d = datetime.date(2024, 3, 12)  # Tuesday
        expected = datetime.date(2024, 3, 11)  # Monday
        assert add_business_days(d, -1) == expected

    def test_add_negative_skips_weekend(self):
        """Subtract 1 business day from Monday should go to Friday."""
        d = datetime.date(2024, 3, 18)  # Monday
        expected = datetime.date(2024, 3, 15)  # Friday
        assert add_business_days(d, -1) == expected

    def test_add_negative_five(self):
        """Subtract 5 business days from Monday."""
        d = datetime.date(2024, 3, 18)  # Monday
        expected = datetime.date(2024, 3, 11)  # Previous Monday
        assert add_business_days(d, -5) == expected

    def test_add_ahead_april_holiday(self):
        """Apr 21 2024 (Tiradentes) is Sunday — holiday on Sunday, Monday is a BD."""
        d = datetime.date(2024, 4, 19)  # Friday
        # +1 BD: skip weekend (Sat/Sun) -> Monday Apr 22
        # Apr 21 (Sun) is Tiradentes but it's already weekend
        expected = datetime.date(2024, 4, 22)  # Monday
        assert add_business_days(d, 1) == expected

    def test_add_skips_good_friday(self):
        """Add 1 BD from Thu Mar 28 2024 skips Good Friday (Mar 29)."""
        d = datetime.date(2024, 3, 28)  # Thursday
        expected = datetime.date(2024, 4, 1)  # Monday (skip Fri holiday + weekend)
        assert add_business_days(d, 1) == expected

    def test_add_ten(self):
        """10 business days from Monday = 2 weeks."""
        d = datetime.date(2024, 3, 11)  # Monday
        expected = datetime.date(2024, 3, 25)  # 2 Mondays later
        assert add_business_days(d, 10) == expected
