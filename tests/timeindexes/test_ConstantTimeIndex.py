from datetime import datetime

from framcore.timeindexes import ConstantTimeIndex


def test_constant_time_index_basic():
    index = ConstantTimeIndex()

    assert index.get_start_time() == datetime.fromisocalendar(1985, 1, 1)
    assert index.get_period_duration().days == 364  # 52 weeks
    assert index.is_52_week_years() is True
    assert index.extrapolate_first_point() is True
    assert index.extrapolate_last_point() is True
