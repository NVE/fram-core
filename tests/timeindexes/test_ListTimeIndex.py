from datetime import UTC, datetime, timedelta, timezone

import numpy as np
import pytest

from framcore.timeindexes import FixedFrequencyTimeIndex, ListTimeIndex


def test_list_time_index_basic():
    datetime_list = [
        datetime(2022, 1, 1, tzinfo=UTC),
        datetime(2022, 1, 2, tzinfo=UTC),
        datetime(2022, 1, 3, tzinfo=UTC),
    ]
    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert len(time_index.get_datetime_list()) == 3
    assert time_index.get_num_periods() == 2
    assert time_index.get_timezone() == UTC
    assert time_index.is_52_week_years() is False
    assert time_index.is_one_year() is False
    assert time_index.is_whole_years() is False
    assert time_index.extrapolate_first_point() is False
    assert time_index.extrapolate_last_point() is False
    assert time_index.is_constant() is False


def test_init_with_single_datetime_entry_raises():
    datetime_list = [
        datetime(2021, 1, 1, tzinfo=UTC),
    ]

    with pytest.raises(ValueError, match="datetime_list must contain more than one element"):
        ListTimeIndex(
            datetime_list=datetime_list,
            is_52_week_years=False,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )


def test_init_unsorted_datetime_list_raises():
    datetime_list = [
        datetime(2022, 1, 2, tzinfo=UTC),
        datetime(2022, 1, 1, tzinfo=UTC),
    ]

    with pytest.raises(ValueError, match="All elements of datetime_list must be smaller/lower than the succeeding element"):
        ListTimeIndex(
            datetime_list=datetime_list,
            is_52_week_years=False,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )


def test_init_datetime_list_with_different_timezone_entries_raises():
    datetime_list = [
        datetime(2022, 1, 1, tzinfo=timezone(timedelta(hours=1))),
        datetime(2022, 1, 2, tzinfo=timezone(timedelta(hours=2))),
    ]

    with pytest.raises(ValueError, match="Datetime objects in datetime_list have differing time zone information"):
        ListTimeIndex(
            datetime_list=datetime_list,
            is_52_week_years=False,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )


def test_init_52_week_years_contain_datetime_week_53_raises():
    datetime_list = [
        datetime.fromisocalendar(2020, 52, 1),
        datetime.fromisocalendar(2020, 53, 1),
    ]

    with pytest.raises(ValueError, match="When is_52_week_years is True, datetime_list should not contain week 53 datetimes."):
        ListTimeIndex(
            datetime_list=datetime_list,
            is_52_week_years=True,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )


@pytest.mark.parametrize(
    ("extrapolate_first_point", "extrapolate_last_point", "expected_result"),
    [
        (True, False, False),
        (False, True, False),
        (True, True, False),
    ],
)
def test_is_one_year_when_extrapolation_enabled_is_not_one_year(extrapolate_first_point: bool, extrapolate_last_point: bool, expected_result: bool):
    datetime_list = [
        datetime.fromisocalendar(2020, 1, 1),
        datetime.fromisocalendar(2021, 1, 1),
    ]

    idx = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=True,
        extrapolate_first_point=extrapolate_first_point,
        extrapolate_last_point=extrapolate_last_point,
    )

    assert idx.is_one_year() is expected_result


@pytest.mark.parametrize(
    ("datetime_list", "expected_result"),
    [
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2021, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2021, 1, 1),
                datetime.fromisocalendar(2022, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2020, 52, 1),
            ],
            False,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2022, 1, 1),
            ],
            False,
        ),
    ],
)
def test_is_one_year_52_week_years(datetime_list: list[datetime], expected_result: bool):
    idx = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert idx.is_one_year() is expected_result


@pytest.mark.parametrize(
    ("datetime_list", "expected_result"),
    [
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2021, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2021, 1, 1),
                datetime.fromisocalendar(2022, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2020, 52, 1),
            ],
            False,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2022, 1, 1),
            ],
            False,
        ),
    ],
)
def test_is_one_year_53_week_years(datetime_list: list[datetime], expected_result: bool):
    idx = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert idx.is_one_year() is expected_result


def test_is_whole_years_when_not_start_of_year_returns_false():
    datetime_list = [
        datetime.fromisocalendar(2020, 2, 1),
        datetime.fromisocalendar(2020, 3, 1),
    ]

    idx = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert idx.is_whole_years() is False


@pytest.mark.parametrize(
    ("datetime_list", "expected_result"),
    [
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2021, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2022, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2021, 1, 1),
                datetime.fromisocalendar(2023, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2025, 1, 1),
                datetime.fromisocalendar(2027, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2020, 52, 1),
            ],
            False,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2021, 50, 4),
            ],
            False,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2020, 52, 7),
            ],
            False,
        ),
        (
            [
                datetime.fromisocalendar(2021, 1, 1),
                datetime.fromisocalendar(2021, 52, 7),
            ],
            False,
        ),
    ],
)
def test_is_whole_years_iso_time_format(datetime_list: list[datetime], expected_result: bool):
    idx = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )
    assert idx.is_whole_years() is expected_result


@pytest.mark.parametrize(
    ("datetime_list", "expected_result"),
    [
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2021, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2021, 1, 1),
                datetime.fromisocalendar(2022, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2022, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2025, 1, 1),
                datetime.fromisocalendar(2027, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2027, 1, 1),
            ],
            True,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2020, 52, 1),
            ],
            False,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2021, 1, 2),
            ],
            False,
        ),
        (
            [
                datetime.fromisocalendar(2020, 1, 1),
                datetime.fromisocalendar(2027, 1, 2),
            ],
            False,
        ),
    ],
)
def test_is_whole_years_52_week_years_format(datetime_list: list[datetime], expected_result: bool):
    idx = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )
    assert idx.is_whole_years() is expected_result


@pytest.mark.parametrize(
    ("vector"),
    [
        (np.array([])),
        (np.array([10, 20, 4])),
        (np.array([1, 2, 3, 4]).reshape(2, 2)),
    ],
)
def test_get_period_average_raises_when_vector_length_not_match_num_periods(vector: np.ndarray):
    datetime_list = [
        datetime.fromisocalendar(2021, 1, 1),
        datetime.fromisocalendar(2021, 3, 1),
        datetime.fromisocalendar(2021, 4, 1),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    start_time = datetime_list[0]
    duration = timedelta(weeks=1)

    with pytest.raises(ValueError) as ex:  # noqa: PT011
        time_index.get_period_average(vector, start_time=start_time, duration=duration, is_52_week_years=False)

    assert str(ex.value).startswith(f"Vector shape {vector.shape} does not match number of periods 2 of timeindex")


def test_get_period_average_uniform_periods():
    datetime_list = [
        datetime.fromisocalendar(2021, 1, 1),
        datetime.fromisocalendar(2021, 1, 2),
        datetime.fromisocalendar(2021, 1, 3),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    vector = np.array([2.0, 4.0])
    start_time = datetime.fromisocalendar(2021, 1, 1)
    duration = timedelta(days=2)

    avg = time_index.get_period_average(vector, start_time, duration, is_52_week_years=False)

    # Since both periods are 1 day, the average should be (2+4)/2 = 3.0
    assert avg == 3.0


def test_get_period_average_with_non_uniform_periods():
    datetime_list = [
        datetime.fromisocalendar(2021, 1, 1),
        datetime.fromisocalendar(2021, 1, 2),
        datetime.fromisocalendar(2021, 1, 4),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    vector = np.array([2.0, 8.0])
    start_time = datetime.fromisocalendar(2021, 1, 1)
    duration = timedelta(days=3)

    avg = time_index.get_period_average(vector, start_time, duration, is_52_week_years=False)

    # Weighted average: (2*1 + 8*2) / 3 = (2 + 16) / 3 = 6.0
    assert avg == 6.0


def test_get_period_average_iso_time_period_contains_week_53():
    datetime_list = [
        datetime.fromisocalendar(2020, 52, 1),
        datetime.fromisocalendar(2020, 53, 3),
        datetime.fromisocalendar(2021, 1, 4),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    vector = np.array([3.0, 9.0])
    start_time = datetime.fromisocalendar(2020, 52, 6)
    duration = timedelta(days=8)

    avg = time_index.get_period_average(vector, start_time, duration, is_52_week_years=False)

    # Weighted average: (3*4 + 9*4) / 8 = (12 + 36) / 8 = 48 / 8 = 6.0
    assert avg == 6.0


def test_get_period_average_52_week_years_period_contains_week_53():
    datetime_list = [
        datetime.fromisocalendar(2020, 52, 1), # 2020 has week 53
        datetime.fromisocalendar(2021, 1, 1),
        datetime.fromisocalendar(2021, 2, 1),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    vector = np.array([3.0, 9.0])
    start_time = datetime.fromisocalendar(2020, 52, 1)
    duration = timedelta(weeks=2)

    avg = time_index.get_period_average(vector, start_time, duration, is_52_week_years=True)

    # Weighted average: (3*1 + 9*1) / 2 = (3 + 9) / 2 = 12 / 2 = 6.0, skipping week 53
    assert avg == 6.0


@pytest.mark.parametrize(
    ("start_time", "duration", "extrapolate_first_point", "extrapolate_last_point", "expected_avg"),
    [
        (
            datetime.fromisocalendar(2021, 1, 1),
            timedelta(days=2),
            True,
            False,
            4.0,
        ),
        (
            datetime.fromisocalendar(2021, 1, 1),
            timedelta(weeks=4),
            True,
            True,
            6.0,
        ),
        (
            datetime.fromisocalendar(2021, 1, 4),
            timedelta(days=16),
            True,
            False,
            5.25,
        ),
        (
            datetime.fromisocalendar(2021, 2, 4),
            timedelta(days=16),
            False,
            True,
            7.0,
        ),
        (
            datetime.fromisocalendar(2021, 4, 1),
            timedelta(days=2),
            False,
            True,
            8.0,
        ),
    ],
)
def test_get_period_average_with_extrapolation(start_time, duration, extrapolate_first_point, extrapolate_last_point, expected_avg):
    datetime_list = [
        datetime.fromisocalendar(2021, 2, 1),
        datetime.fromisocalendar(2021, 3, 1),
        datetime.fromisocalendar(2021, 4, 1),
    ]

    vector = np.array([4.0, 8.0])

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=extrapolate_first_point,
        extrapolate_last_point=extrapolate_last_point,
    )

    avg = time_index.get_period_average(vector, start_time, duration, is_52_week_years=False)
    assert avg == expected_avg


@pytest.mark.parametrize(
    ("start_time", "duration", "raises_message"),
    [
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=2), "start_time"),
        (datetime.fromisocalendar(2021, 3, 1), timedelta(weeks=2), "End time"),
        (datetime.fromisocalendar(2021, 4, 2), timedelta(weeks=2), "End time"),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(days=2), "start_time"),
    ],
)
def test_get_period_average_no_extrapolation_and_request_period_out_of_bounds_raises(start_time, duration, raises_message):
    datetime_list = [
        datetime.fromisocalendar(2021, 2, 1),
        datetime.fromisocalendar(2021, 3, 1),
        datetime.fromisocalendar(2021, 4, 1),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    with pytest.raises(ValueError, match=raises_message):
        time_index.get_period_average(np.array([4.0, 8.0]), start_time, duration, is_52_week_years=False)


def test_write_into_fixed_frequency_uniform_periods():
    datetime_list = [
        datetime.fromisocalendar(2021, 1, 1),
        datetime.fromisocalendar(2021, 3, 1),
        datetime.fromisocalendar(2021, 5, 1),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    input_vector = np.array([10.0, 20.0])
    target_vector = np.zeros(2)

    target_timeindex = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2021, 1, 1),
        period_duration=timedelta(weeks=2),
        num_periods=2,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    time_index.write_into_fixed_frequency(target_vector, target_timeindex, input_vector)

    np.testing.assert_array_equal(target_vector, np.array([10.0, 20.0]))


def test_write_into_fixed_frequency_non_uniform_periods():
    datetime_list = [
        datetime.fromisocalendar(2021, 1, 1),
        datetime.fromisocalendar(2021, 2, 1),
        datetime.fromisocalendar(2021, 4, 1),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    input_vector = np.array([5.0, 7.0], dtype=np.float32)
    target_vector = np.zeros(3, dtype=np.float32)

    target_timeindex = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2021, 1, 1),
        period_duration=timedelta(weeks=1),
        num_periods=3,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    time_index.write_into_fixed_frequency(target_vector, target_timeindex, input_vector)

    np.testing.assert_array_equal(target_vector, np.array([5.0, 7.0, 7.0], dtype=np.float32))


def test_write_into_fixed_frequency_partial_overlap():
    datetime_list = [
        datetime.fromisocalendar(2021, 3, 1),
        datetime.fromisocalendar(2021, 4, 1),
        datetime.fromisocalendar(2021, 6, 1),
    ]

    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=True,
        extrapolate_last_point=True,
    )

    input_vector = np.array([4.0, 8.0], dtype=np.float32)
    target_vector = np.zeros(5, dtype=np.float32)

    target_timeindex = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2021, 1, 1),
        period_duration=timedelta(weeks=1),
        num_periods=5,
        is_52_week_years=False,
        extrapolate_first_point=True,
        extrapolate_last_point=True,
    )

    time_index.write_into_fixed_frequency(target_vector, target_timeindex, input_vector)

    np.testing.assert_array_equal(target_vector, np.array([4.0, 4.0, 4.0, 8.0, 8.0], dtype=np.float32))


@pytest.mark.parametrize(
    ("datetime_list", "extrapolate_first_point", "extrapolate_last_point", "expected_is_constant"),
    [
        (
            [
                datetime.fromisocalendar(2022, 1, 1),
                datetime.fromisocalendar(2022, 1, 2),
            ],
            True,
            True,
            True,
        ),
        (
            [
                datetime.fromisocalendar(2022, 1, 1),
                datetime.fromisocalendar(2022, 1, 2),
            ],
            False,
            False,
            False,
        ),
        (
            [
                datetime.fromisocalendar(2022, 1, 1),
                datetime.fromisocalendar(2022, 1, 2),
                datetime.fromisocalendar(2022, 1, 3),
            ],
            True,
            True,
            False,
        ),
    ],
)
def test_is_constant_when_single_period_and_extrapolation_both_points_then_true(
    datetime_list,
    extrapolate_first_point,
    extrapolate_last_point,
    expected_is_constant,
):
    time_index = ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=extrapolate_first_point,
        extrapolate_last_point=extrapolate_last_point,
    )

    assert time_index.is_constant() is expected_is_constant
