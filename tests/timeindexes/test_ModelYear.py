from datetime import datetime, timedelta

from framcore.timeindexes import ModelYear


def test_model_year_basic():
    model_year = ModelYear(year=2021)

    assert model_year.get_start_time() == datetime(2021, 1, 4)
    assert model_year.get_period_duration() == timedelta(days=364)
    assert model_year.is_52_week_years() is True
    assert model_year.extrapolate_first_point() is False
    assert model_year.extrapolate_last_point() is False
    assert model_year.get_num_periods() == 1
    assert model_year.get_stop_time() == datetime(2022, 1, 3)
