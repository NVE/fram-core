from datetime import datetime, timedelta

import numpy as np
import pytest

from framcore.timeindexes import FixedFrequencyTimeIndex
from framcore.timevectors import ReferencePeriod


def test_init_valid_inputs():
    start_time = datetime.fromisocalendar(2021, 1, 4)
    period_duration = timedelta(days=7)
    num_periods = 52

    idx = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert idx.get_start_time() == start_time
    assert idx.get_period_duration() == period_duration
    assert idx.get_num_periods() == num_periods
    assert idx.is_52_week_years() is False
    assert idx.extrapolate_first_point() is False
    assert idx.extrapolate_last_point() is False


@pytest.mark.parametrize("num_periods", [0, -10])
def test_init_invalid_num_periods(num_periods):
    with pytest.raises(ValueError, match="num_periods must be a positive integer"):
        FixedFrequencyTimeIndex(
            start_time=datetime(2021, 1, 4),
            period_duration=timedelta(days=7),
            num_periods=num_periods,
            is_52_week_years=False,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )


@pytest.mark.parametrize("period_duration", [timedelta(seconds=0), timedelta(microseconds=999999)])
def test_init_invalid_period_duration_too_short(period_duration):
    with pytest.raises(ValueError, match="period_duration must be at least one second"):
        FixedFrequencyTimeIndex(
            start_time=datetime(2021, 1, 4),
            period_duration=period_duration,
            num_periods=1,
            is_52_week_years=False,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )


def test_init_invalid_period_duration_not_integer_seconds():
    with pytest.raises(ValueError, match="period_duration must be a whole number of seconds"):
        FixedFrequencyTimeIndex(
            start_time=datetime(2021, 1, 4),
            period_duration=timedelta(seconds=1.5),
            num_periods=1,
            is_52_week_years=False,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )


def test_init_52_week_years_start_date_can_not_be_in_week_53():
    start_time = datetime.fromisocalendar(2020, 53, 1)

    with pytest.raises(ValueError, match="Week of start_time must not be 53 when is_52_week_years is True"):
        FixedFrequencyTimeIndex(
            start_time=start_time,
            period_duration=timedelta(days=7),
            num_periods=1,
            is_52_week_years=True,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )


@pytest.mark.parametrize(
    ("num_periods", "extrapolate_first_point", "extrapolate_last_point", "expected_is_constant"),
    [
        (1, True, True, True),
        (1, False, True, False),
        (1, True, False, False),
        (2, True, True, False),
    ],
)
def test_is_constant_when_single_period_and_extrapolation_both_points_then_true(
    num_periods, extrapolate_first_point, extrapolate_last_point, expected_is_constant,
):
    time_index = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2022, 1, 1),
        period_duration=timedelta(days=1),
        num_periods=num_periods,
        is_52_week_years=False,
        extrapolate_first_point=extrapolate_first_point,
        extrapolate_last_point=extrapolate_last_point,
    )

    assert time_index.is_constant() is expected_is_constant


@pytest.mark.parametrize(
    ("start_time", "num_periods", "period_duration", "expected_stop"),
    [
        # One 52-week year
        (
            datetime.fromisocalendar(2021, 1, 1),
            52,
            timedelta(days=7),
            datetime.fromisocalendar(2022, 1, 1),
        ),
        # Five 52-week years
        (
            datetime.fromisocalendar(2021, 1, 1),
            52 * 5,
            timedelta(days=7),
            datetime.fromisocalendar(2026, 1, 1),
        ),
        # 53-week year
        (
            datetime.fromisocalendar(2020, 1, 1),
            52,
            timedelta(days=7),
            datetime.fromisocalendar(2021, 1, 1),
        ),
        # Two years with one 53-week year
        (
            datetime.fromisocalendar(2019, 1, 1),
            52 * 2,
            timedelta(days=7),
            datetime.fromisocalendar(2021, 1, 1),
        ),
        # Seven years with two 53-week years
        (
            datetime.fromisocalendar(2020, 1, 1),
            52 * 7,
            timedelta(days=7),
            datetime.fromisocalendar(2027, 1, 1),
        ),
    ],
)
def test_get_stop_time_52_week_years(start_time, num_periods, period_duration, expected_stop):
    idx = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert idx.get_stop_time() == expected_stop


@pytest.mark.parametrize(
    ("start_time", "num_periods", "period_duration", "expected_stop"),
    [
        # One 52-week year
        (
            datetime.fromisocalendar(2021, 1, 1),
            52,
            timedelta(days=7),
            datetime.fromisocalendar(2022, 1, 1),
        ),
        # Five 52-week years
        (
            datetime.fromisocalendar(2021, 1, 1),
            52 * 5,
            timedelta(days=7),
            datetime.fromisocalendar(2026, 1, 1),
        ),
        # 53-week year
        (
            datetime.fromisocalendar(2020, 1, 1),
            53,
            timedelta(days=7),
            datetime.fromisocalendar(2021, 1, 1),
        ),
        # Two years with one 53-week year
        (
            datetime.fromisocalendar(2019, 1, 1),
            52 + 53,
            timedelta(days=7),
            datetime.fromisocalendar(2021, 1, 1),
        ),
        # Seven years with two 53-week years
        (
            datetime.fromisocalendar(2020, 1, 1),
            52 * 5 + 53 * 2,
            timedelta(days=7),
            datetime.fromisocalendar(2027, 1, 1),
        ),
    ],
)
def test_get_stop_time_iso_years(start_time, num_periods, period_duration, expected_stop):
    idx = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert idx.get_stop_time() == expected_stop


def test_is_whole_years_when_not_start_of_year_returns_false():
    start_time = datetime.fromisocalendar(2021, 2, 1)

    index = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=timedelta(weeks=52),
        num_periods=1,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert index.is_whole_years() is False


@pytest.mark.parametrize(
    ("start_time", "period_duration", "num_periods", "expected_result"),
    [
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 53, True),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 53 + 52, True),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 53 * 2 + 52 * 5, True),  # 2020-2026
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52, True),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52 * 2, True),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52 * 5 + 53, True),  # 2021-2026
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 52, False),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 53 + 52 - 1, False),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 53 + 52 + 1, False),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52 - 1, False),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52 + 1, False),
    ],
)
def test_is_whole_years_iso_time_format(start_time, period_duration, num_periods, expected_result: bool):
    idx = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert idx.is_whole_years() is expected_result


@pytest.mark.parametrize(
    ("start_time", "period_duration", "num_periods", "expected_result"),
    [
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 52, True),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 52 * 2, True),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 52 * 7, True),  # 2020-2026
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52, True),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52 * 2, True),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52 * 6, True),  # 2021-2026
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 52 + 1, False),
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 52 - 1, False),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52 + 1, False),
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52 - 1, False),
    ],
)
def test_is_whole_years_52_week_years_format(start_time, period_duration, num_periods, expected_result: bool):
    idx = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    assert idx.is_whole_years() is expected_result


@pytest.mark.parametrize(
    ("start_time", "num_periods", "expected_num_years"),
    [
        (datetime(1980, 12, 29), 52, 1),
        (datetime(1980, 12, 29), 52 + 52, 2),
        (datetime(1980, 12, 29), 52 * 10, 10),
    ],
    ids=[
        "one_year",
        "two_years",
        "ten_years",
    ],
)
def test_get_reference_period_with_52_week_time_format(start_time: datetime, num_periods: int, expected_num_years: int):
    is_model_time = True  # Model time with 52-weeks years
    period_duration = timedelta(weeks=1)

    time_index = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        is_52_week_years=is_model_time,
        num_periods=num_periods,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    reference_period = time_index.get_reference_period()

    assert reference_period is not None
    assert reference_period.get_num_years() == expected_num_years


@pytest.mark.parametrize(
    ("start_time", "num_periods", "expected_num_years"),
    [
        (datetime.fromisocalendar(1981, 1, 1), 53, 1),
        (datetime.fromisocalendar(1981, 1, 1), 53 + 52, 2),
        (datetime.fromisocalendar(1982, 1, 1), 52, 1),
        (datetime.fromisocalendar(1982, 1, 1), 52 + 52, 2),
    ],
)
def test_get_reference_period_with_isotime_format(start_time: datetime, num_periods: int, expected_num_years: int):
    is_model_time = False  # ISO-time, possible to have week 53
    period_duration = timedelta(weeks=1)

    time_index = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        is_52_week_years=is_model_time,
        num_periods=num_periods,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    reference_period = time_index.get_reference_period()

    assert reference_period is not None
    assert reference_period.get_num_years() == expected_num_years


def test_get_reference_period_if_not_whole_years_then_reference_period_is_none():
    is_model_time = True  # Model time with 52-weeks years
    start_time = datetime(1980, 12, 29)  # Monday, week 1 of 1981, a 52-weeks year
    period_duration = timedelta(weeks=1)
    num_periods = 51  # Not whole year

    time_index = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        is_52_week_years=is_model_time,
        num_periods=num_periods,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    reference_period = time_index.get_reference_period()

    assert reference_period is None


@pytest.mark.parametrize(
    ("start_time", "period_duration", "num_periods", "is_52_week_years", "expected_result"),
    [
        # Modell time checks (52-week years)
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 52, True, True),  # Is one-year index modell time
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 52, True, True),  # Is one-year index modell time, even if 2020 is a 53-week year
        (datetime.fromisocalendar(2020, 2, 1), timedelta(weeks=1), 52, True, False),  # Not start of year
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=2), 52, True, False),  # Longer than one year
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 53, True, False),  # 2020 is a 53-week year, but model time is allways 52 weeks
        # ISO-time checks (52 or 53-week years)
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 53, False, True),  # 2020 is a 53-week year
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=1), 52, False, False),  # ISO-time 2020 is a 53-week year, not 52
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=1), 53, False, False),  # ISO-time 2021 is a 52-week year, not 53
        (datetime.fromisocalendar(2020, 2, 1), timedelta(weeks=1), 53, False, False),  # Not start of year
        (datetime.fromisocalendar(2020, 1, 1), timedelta(weeks=2), 53, False, False),  # Longer than one year
    ],
)
def test_is_one_year(start_time, period_duration, num_periods, is_52_week_years, expected_result):
    index = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=is_52_week_years,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    result = index.is_one_year()

    assert result is expected_result, f"Expected is_one_year to return {expected_result} for a one-year index."


@pytest.mark.parametrize(
    ("vector"),
    [
        (np.array([])),
        (np.array([10, 20, 4])),
        (np.array([1, 2, 3, 4]).reshape(2, 2)),
    ],
)
def test_get_period_average_raises_when_vector_length_not_match_num_periods(vector: np.ndarray):
    index = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2021, 1, 1),
        period_duration=timedelta(weeks=1),
        num_periods=2,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    start_time = datetime.fromisocalendar(2021, 1, 1)
    duration = timedelta(weeks=1)

    with pytest.raises(ValueError) as ex:  # noqa: PT011
        index.get_period_average(vector, start_time=start_time, duration=duration, is_52_week_years=True)

    assert str(ex.value).startswith(f"Vector shape {vector.shape} does not match number of periods 2 of timeindex")


@pytest.mark.parametrize(
    ("start_time", "duration", "expected_average"),
    [
        (datetime.fromisocalendar(2020, 51, 1), timedelta(weeks=2), (10.0 + 20.0) / 2),
        (datetime.fromisocalendar(2020, 52, 1), timedelta(weeks=3), (20.0 + 30.0 + 40.0) / 3),  # contains week 53
    ],
)
def test_get_period_average_iso_time_format(start_time: datetime, duration: timedelta, expected_average: float):
    index = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2020, 51, 1),
        period_duration=timedelta(weeks=1),
        num_periods=4,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    vector = np.array([10.0, 20.0, 30.0, 40.0])

    average = index.get_period_average(vector, start_time=start_time, duration=duration, is_52_week_years=False)

    assert average == expected_average


@pytest.mark.parametrize(
    ("start_time", "duration", "expected_average"),
    [
        (datetime.fromisocalendar(2020, 51, 1), timedelta(weeks=2), (10.0 + 20.0) / 2),
        (datetime.fromisocalendar(2020, 52, 1), timedelta(weeks=3), (20.0 + 30.0 + 40.0) / 3),  # contains week 53
        (datetime.fromisocalendar(2021, 1, 1), timedelta(weeks=2), (30.0 + 40.0) / 2),  # just after week 53
    ],
)
def test_get_period_average_52_week_years(start_time: datetime, duration: timedelta, expected_average: float):
    index = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2020, 51, 1),
        period_duration=timedelta(weeks=1),
        num_periods=4,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    vector = np.array([10.0, 20.0, 30.0, 40.0])

    average = index.get_period_average(vector, start_time=start_time, duration=duration, is_52_week_years=True)

    assert average == expected_average


@pytest.mark.parametrize(
    ("period_duration", "num_periods", "expected_total_duration"),
    [
        (timedelta(weeks=1), 1, timedelta(weeks=1)),
        (timedelta(days=1), 1, timedelta(days=1)),
        (timedelta(hours=12), 4, timedelta(days=2)),
    ],
)
def test_get_total_duration(period_duration: timedelta, num_periods: int, expected_total_duration: timedelta):
    index = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2021, 1, 1),
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    total_duration = index.total_duration()

    assert total_duration == expected_total_duration


def test_copy_as_reference_period_iso_time():
    index = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2020, 1, 1),
        period_duration=timedelta(weeks=1),
        num_periods=53,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    reference_period = ReferencePeriod(start_year=2020, num_years=3)

    result_index = index.copy_as_reference_period(reference_period=reference_period)

    assert result_index.get_start_time() == datetime.fromisocalendar(reference_period.get_start_year(), 1, 1)
    assert result_index.get_num_periods() == 1
    assert result_index.get_period_duration() == timedelta(weeks=53 + 52 * 2)  # 3 years including one 53-week year


def test_copy_as_reference_period_52_week_years():
    index = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2020, 1, 1),
        period_duration=timedelta(weeks=1),
        num_periods=52,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    reference_period = ReferencePeriod(start_year=2020, num_years=3)

    result_index = index.copy_as_reference_period(reference_period=reference_period)

    assert result_index.get_start_time() == datetime.fromisocalendar(reference_period.get_start_year(), 1, 1)
    assert result_index.get_num_periods() == 1
    assert result_index.get_period_duration() == timedelta(weeks=52 * 3)  # 3 years model time


def test_copy_as_reference_period_when_reference_period_is_none_raises():
    index = FixedFrequencyTimeIndex(
        start_time=datetime.fromisocalendar(2021, 1, 1),
        period_duration=timedelta(days=7),
        num_periods=10,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    with pytest.raises(ValueError, match="Cannot copy as reference period when provided reference_period is None"):
        index.copy_as_reference_period(reference_period=None)


@pytest.mark.parametrize(
    ("start_time","period_duration", "num_periods", "expected_datetimes"),
    [
        (
            datetime.fromisocalendar(2020, 52, 1),
            timedelta(weeks=1),
            3,
            [
                datetime.fromisocalendar(2020, 52, 1),
                datetime.fromisocalendar(2020, 53, 1),
                datetime.fromisocalendar(2021, 1, 1),
                datetime.fromisocalendar(2021, 2, 1),
            ],
        ),
        (
            datetime.fromisocalendar(2020, 52, 6),
            timedelta(days=1),
            3,
            [
                datetime.fromisocalendar(2020, 52, 6),
                datetime.fromisocalendar(2020, 52, 7),
                datetime.fromisocalendar(2020, 53, 1),
                datetime.fromisocalendar(2020, 53, 2),
            ],
        ),
        (
            datetime.fromisocalendar(2020, 52, 7),
            timedelta(hours=8),
            4,
            [
                datetime(2020, 12, 27, 0, 0),
                datetime(2020, 12, 27, 8, 0),
                datetime(2020, 12, 27, 16, 0),
                datetime(2020, 12, 28, 0, 0),
                datetime(2020, 12, 28, 8, 0),
            ],
        ),
    ],
)
def test_get_datetime_list_iso_time(start_time: datetime, period_duration: timedelta, num_periods: int, expected_datetimes: list[datetime]):
    index = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    datetime_list = index.get_datetime_list()

    assert np.array_equal(datetime_list, np.array(expected_datetimes))

@pytest.mark.parametrize(
    ("start_time", "period_duration", "num_periods", "expected_datetimes"),
    [
        (
            datetime.fromisocalendar(2020, 52, 1),
            timedelta(weeks=1),
            3,
            [
                datetime.fromisocalendar(2020, 52, 1),
                datetime.fromisocalendar(2021, 1, 1),
                datetime.fromisocalendar(2021, 2, 1),
                datetime.fromisocalendar(2021, 3, 1),
            ],
        ),
        (
            datetime.fromisocalendar(2020, 52, 6),
            timedelta(days=1),
            3,
            [
                datetime.fromisocalendar(2020, 52, 6),
                datetime.fromisocalendar(2020, 52, 7),
                datetime.fromisocalendar(2021, 1, 1),
                datetime.fromisocalendar(2021, 1, 2),
            ],
        ),
        (
            datetime.fromisocalendar(2020, 52, 7),
            timedelta(hours=8),
            4,
            [
                datetime(2020, 12, 27, 0, 0),
                datetime(2020, 12, 27, 8, 0),
                datetime(2020, 12, 27, 16, 0),
                datetime(2021, 1, 4, 0, 0),
                datetime(2021, 1, 4, 8, 0),
            ],
        ),
    ],
)
def test_get_datetime_list_52_week_years(start_time: datetime, period_duration: timedelta, num_periods: int, expected_datetimes: list[datetime]):
    index = FixedFrequencyTimeIndex(
        start_time=start_time,
        period_duration=period_duration,
        num_periods=num_periods,
        is_52_week_years=True,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )

    datetime_list = index.get_datetime_list()

    assert np.array_equal(datetime_list, np.array(expected_datetimes))
