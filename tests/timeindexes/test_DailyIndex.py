from datetime import datetime, timedelta

from framcore.timeindexes import DailyIndex


def test_daily_index_basic():
    start_year = 2021
    index = DailyIndex(start_year=start_year, num_years=1, is_52_week_years=True)

    assert index.get_start_time() == datetime(2021, 1, 4)
    assert index.get_period_duration() == timedelta(days=1)
    assert index.is_52_week_years() is True
    assert index.extrapolate_first_point() is False
    assert index.extrapolate_last_point() is False
    assert index.get_num_periods() == 364  # 52 weeks
    assert index.get_stop_time() == datetime(2022, 1, 3)

def test_daily_index_iso_year():
    start_year = 2021
    index = DailyIndex(start_year=start_year, num_years=1, is_52_week_years=False)

    assert index.get_start_time() == datetime(2021, 1, 4)
    assert index.get_period_duration() == timedelta(days=1)
    assert index.is_52_week_years() is False
    assert index.extrapolate_first_point() is False
    assert index.extrapolate_last_point() is False
    assert index.get_num_periods() == 364 # 2021 is a 52-week year
    assert index.get_stop_time() == datetime(2022, 1, 3)

def test_daily_index_multiple_years():
    start_year = 2020
    num_years = 3
    index = DailyIndex(start_year=start_year, num_years=num_years, is_52_week_years=False)

    assert index.get_start_time() == datetime(2019, 12, 30)
    assert index.get_period_duration() == timedelta(days=1)
    assert index.is_52_week_years() is False
    assert index.extrapolate_first_point() is False
    assert index.extrapolate_last_point() is False
    assert index.get_num_periods() == 1099
    assert index.get_stop_time() == datetime(2023, 1, 2)
