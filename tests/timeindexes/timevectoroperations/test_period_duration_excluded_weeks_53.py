from datetime import datetime, timedelta

import pytest

from framcore.timeindexes._time_vector_operations import _period_duration_excluded_weeks_53


@pytest.mark.parametrize(
    ("start_time", "end_time", "expected_duration"),
    [
        # No week 53 in period, nothing to exclude
        (datetime.fromisocalendar(2021, 1, 1), datetime.fromisocalendar(2022, 1, 1), timedelta(weeks=52)),
        # Period includes one week 53, one week should be excluded
        (datetime.fromisocalendar(2020, 1, 1), datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=52)),
        # Period includes two weeks 53, two weeks should be excluded
        (datetime.fromisocalendar(2020, 1, 1), datetime.fromisocalendar(2027, 1, 1), timedelta(weeks=52*7)),
        # Period is exactly week 53, duration is 0
        (datetime.fromisocalendar(2020, 53, 1), datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=0)),
        # Period is within week 53
        (datetime.fromisocalendar(2020, 53, 1), datetime.fromisocalendar(2020, 53, 3), timedelta(weeks=0)),
        # Period with zero duration
        (datetime.fromisocalendar(2021, 1, 1), datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=0)),
    ],
    ids=[
        "No week 53 in period",
        "One week 53 in period",
        "Two weeks 53 in period",
        "Period is exactly one week 53",
        "Period is within week 53",
        "Zero duration period",
    ],
)
def test_period_duration_excluded_weeks_53_valid_inputs(start_time: datetime, end_time: datetime, expected_duration: timedelta):
    result = _period_duration_excluded_weeks_53(start_time, end_time)

    assert result == expected_duration, (
        f"Expected {expected_duration}, got {result} for period {start_time} to {end_time}"
    )

def test_period_duration_excluded_weeks_53_end_time_before_start_time_raises_value_error():
    start_time = datetime.fromisocalendar(2021, 1, 1)
    end_time = start_time - timedelta(seconds=1)

    with pytest.raises(ValueError, match="end_time must be after or equal to start_time"):
        _period_duration_excluded_weeks_53(start_time, end_time)