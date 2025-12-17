from datetime import datetime, timedelta

import pytest

from framcore.timeindexes import AverageYearRange


def test_average_year_range_basic():
    start_year = 2021
    num_years = 3
    expected_start = datetime(2021, 1, 4)
    expected_duration = timedelta(days=(364+364+364))  # only 52-week years

    avg_range = AverageYearRange(start_year, num_years)

    assert avg_range.get_start_time() == expected_start
    assert avg_range.get_period_duration() == expected_duration
    assert avg_range.is_52_week_years() is False
    assert avg_range.extrapolate_first_point() is False
    assert avg_range.extrapolate_last_point() is False

def test_average_year_range_with_53_week_year():
    start_year = 2019
    num_years = 3
    expected_start = datetime(2018, 12, 31)
    expected_duration = timedelta(days=(364+371+364))  # includes one 53-week year

    avg_range = AverageYearRange(start_year, num_years)

    assert avg_range.get_start_time() == expected_start
    assert avg_range.get_period_duration() == expected_duration
    assert avg_range.is_52_week_years() is False
    assert avg_range.extrapolate_first_point() is False
    assert avg_range.extrapolate_last_point() is False

def test_average_year_range_zero_years():
    with pytest.raises(ValueError):  # noqa: PT011
        AverageYearRange(2020, 0)

def test_average_year_range_negative_years():
    with pytest.raises(ValueError):  # noqa: PT011
        AverageYearRange(2020, -3)
