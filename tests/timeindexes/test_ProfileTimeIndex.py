from datetime import timedelta

import pytest

from framcore.timeindexes import ProfileTimeIndex


@pytest.mark.parametrize(
    ("start_year", "num_years", "period_duration", "is_52_week_years", "expected_num_periods", "expected_period_duration"),
    [
        (2020, 1, timedelta(days=7), False, 53, timedelta(days=7)),
        (2021, 1, timedelta(days=7), False, 52, timedelta(days=7)),
        (2020, 2, timedelta(days=7), False, 53 + 52, timedelta(days=7)),
        (2020, 7, timedelta(days=7), False, 52 * 5 + 53 * 2, timedelta(days=7)),
        (2021, 2, timedelta(days=7), False, 52 + 52, timedelta(days=7)),
        (2020, 1, timedelta(days=7), True, 52, timedelta(days=7)),
        (2021, 1, timedelta(days=7), True, 52, timedelta(days=7)),
        (2020, 2, timedelta(days=7), True, 52 + 52, timedelta(days=7)),
        (2020, 7, timedelta(days=7), True, 52 * 7, timedelta(days=7)),
        (2021, 2, timedelta(days=7), True, 52 + 52, timedelta(days=7)),
    ],
)
def test_profile_time_index_valid_inputs(
    start_year,
    num_years,
    period_duration,
    is_52_week_years,
    expected_num_periods,
    expected_period_duration,
):
    idx = ProfileTimeIndex(
        start_year=start_year,
        num_years=num_years,
        period_duration=period_duration,
        is_52_week_years=is_52_week_years,
    )

    assert idx.get_num_periods() == expected_num_periods
    assert idx.get_period_duration() == expected_period_duration
    assert idx.is_52_week_years() is is_52_week_years
    assert idx.extrapolate_first_point() is False
    assert idx.extrapolate_last_point() is False

    start_date = idx.get_start_time().isocalendar()
    assert start_date.week == 1
    assert start_date.weekday == 1
    assert idx.get_stop_time().isocalendar().year == start_date.year + num_years
    assert idx.get_stop_time().isocalendar().week == 1
    assert idx.get_stop_time().isocalendar().weekday == 1


def test_profile_time_index_incompatible_period_duration_raises():
    with pytest.raises(ValueError, match="Number of periods derived from input arguments must be an integer"):
        ProfileTimeIndex(
            start_year=2021,
            num_years=1,
            period_duration=timedelta(days=10),
            is_52_week_years=True,
        )
