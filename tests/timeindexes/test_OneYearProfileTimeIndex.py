from datetime import timedelta

import pytest

from framcore.timeindexes import OneYearProfileTimeIndex


@pytest.mark.parametrize(
    ("is_52_week_years", "expected_num_periods"),
    [
        (True, 52),
        (False, 53),
    ],
)
def test_init_week_year(is_52_week_years: bool, expected_num_periods: int):
    period = timedelta(days=7)

    idx = OneYearProfileTimeIndex(period_duration=period, is_52_week_years=is_52_week_years)

    assert idx.get_period_duration() == period
    assert idx.is_52_week_years() is is_52_week_years
    assert idx.get_num_periods() == expected_num_periods
    assert idx.extrapolate_first_point() is False
    assert idx.extrapolate_last_point() is False

    start_date = idx.get_start_time().isocalendar()
    assert start_date.week == 1
    assert start_date.weekday == 1

    assert idx.get_stop_time().isocalendar().year == start_date.year + 1
    assert idx.get_stop_time().isocalendar().week == 1
    assert idx.get_stop_time().isocalendar().weekday == 1


@pytest.mark.parametrize(
    ("period", "is_52_week_years"),
    [
        (timedelta(days=10), True),
        (timedelta(days=10), False),
    ],
)
def test_init_invalid_period_duration(period, is_52_week_years):
    with pytest.raises(ValueError, match="Number of periods derived from input arguments must be an integer/whole number"):
        OneYearProfileTimeIndex(period_duration=period, is_52_week_years=is_52_week_years)
