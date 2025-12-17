from datetime import datetime, timedelta

import pytest

from framcore.timeindexes import SinglePeriodTimeIndex


@pytest.mark.parametrize(
    ("start_time", "period_duration", "is_52_week_years", "extrapolate_first_point", "extrapolate_last_point", "stop_time"),
    [
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=53), False, True, True, datetime.fromisocalendar(2021, 1, 1)),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=53), False, True, True, datetime.fromisocalendar(2022, 2, 1)),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=105), False, True, True, datetime.fromisocalendar(2022, 1, 1)),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=53), True, True, True, datetime.fromisocalendar(2021, 2, 1)),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=53), True, True, True, datetime.fromisocalendar(2022, 2, 1)),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=105), True, True, True, datetime.fromisocalendar(2022, 2, 1)),
    ],
)
def test_single_period_time_index_valid_inputs(
    start_time,
    period_duration,
    is_52_week_years,
    extrapolate_first_point,
    extrapolate_last_point,
    stop_time,
):
    idx = SinglePeriodTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        is_52_week_years=is_52_week_years,
        extrapolate_first_point=extrapolate_first_point,
        extrapolate_last_point=extrapolate_last_point,
    )

    assert idx.get_num_periods() == 1
    assert idx.get_start_time() == start_time
    assert idx.get_period_duration() == period_duration
    assert idx.is_52_week_years() is is_52_week_years
    assert idx.extrapolate_first_point() is extrapolate_first_point
    assert idx.extrapolate_last_point() is extrapolate_last_point
    assert idx.get_stop_time() == stop_time
