from datetime import datetime, timedelta

import pytest

from framcore.timeindexes import WeeklyIndex


@pytest.mark.parametrize(
    ("start_year", "num_years", "is_52_week_years", "expected_num_periods", "expected_start", "expected_stop"),
    [
        (2020, 1, False, 53, datetime.fromisocalendar(2020, 1, 1), datetime.fromisocalendar(2021, 1, 1)),
        (2020, 2, False, 53 + 52, datetime.fromisocalendar(2020, 1, 1), datetime.fromisocalendar(2022, 1, 1)),
        (2020, 7, False, 52 * 5 + 53 * 2, datetime.fromisocalendar(2020, 1, 1), datetime.fromisocalendar(2027, 1, 1)),
        (2021, 1, False, 52, datetime.fromisocalendar(2021, 1, 1), datetime.fromisocalendar(2022, 1, 1)),
        (2021, 2, False, 52 * 2, datetime.fromisocalendar(2021, 1, 1), datetime.fromisocalendar(2023, 1, 1)),
        (2020, 1, True, 52, datetime.fromisocalendar(2020, 1, 1), datetime.fromisocalendar(2021, 1, 1)),
        (2020, 2, True, 52 + 52, datetime.fromisocalendar(2020, 1, 1), datetime.fromisocalendar(2022, 1, 1)),
        (2020, 7, True, 52 * 7, datetime.fromisocalendar(2020, 1, 1), datetime.fromisocalendar(2027, 1, 1)),
        (2021, 1, True, 52, datetime.fromisocalendar(2021, 1, 1), datetime.fromisocalendar(2022, 1, 1)),
        (2021, 2, True, 52 * 2, datetime.fromisocalendar(2021, 1, 1), datetime.fromisocalendar(2023, 1, 1)),
    ],
)
def test_weekly_index_valid_inputs(start_year, num_years, is_52_week_years, expected_num_periods, expected_start, expected_stop):
    idx = WeeklyIndex(
        start_year=start_year,
        num_years=num_years,
        is_52_week_years=is_52_week_years,
    )

    assert idx.get_num_periods() == expected_num_periods
    assert idx.get_start_time() == expected_start
    assert idx.get_period_duration() == timedelta(weeks=1)
    assert idx.is_52_week_years() is is_52_week_years
    assert idx.get_stop_time() == expected_stop
