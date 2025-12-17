from datetime import datetime, timedelta

from framcore.timeindexes import IsoCalendarDay


def test_iso_calendar_day_basic():
    index = IsoCalendarDay(year=2021, week=15, day=6)  # 2021-04-17

    assert index.get_start_time() == datetime(2021, 4, 17)
    assert index.get_period_duration() == timedelta(days=1)
    assert index.is_52_week_years() is False
    assert index.extrapolate_first_point() is False
    assert index.extrapolate_last_point() is False
    assert index.get_num_periods() == 1
    assert index.get_stop_time() == datetime(2021, 4, 18)
