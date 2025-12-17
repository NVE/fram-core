from datetime import datetime, timedelta

import numpy as np
import pytest
from numpy.typing import NDArray

from framcore.timeindexes import ListTimeIndex, TimeIndex
from framcore.timevectors import ListTimeVector, ReferencePeriod


def _list_timeindex(num_periods: int = 3) -> ListTimeIndex:
    start = datetime.fromisocalendar(2021, 1, 1)
    datetime_list = [start + timedelta(days=i) for i in range(num_periods + 1)]

    return ListTimeIndex(
        datetime_list=datetime_list,
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )


def _other_list_timeindex(num_periods: int = 3) -> ListTimeIndex:
    return ListTimeIndex(
        datetime_list=[
            datetime.fromisocalendar(2021, 2, 1),
            datetime.fromisocalendar(2021, 2, 2),
            datetime.fromisocalendar(2021, 2, 3),
            datetime.fromisocalendar(2021, 2, 4),
        ],
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )


@pytest.mark.parametrize(
    ("is_max_level", "is_zero_one_profile"),
    [
        (None, None),
        (True, True),
        (False, False),
        (True, False),
        (False, True),
    ],
)
def test_init_must_be_either_level_or_profile(is_max_level: bool | None, is_zero_one_profile: bool | None):
    with pytest.raises(ValueError, match="Invalid input arguments for ListTimeVector"):
        ListTimeVector(
            timeindex=_list_timeindex(),
            vector=np.array([2.0, 3.0, 4.0], dtype=np.float64),
            unit=None,
            is_max_level=is_max_level,
            is_zero_one_profile=is_zero_one_profile,
        )


def test_init_input_vector_shape_must_match_timeindex():
    timeindex = _list_timeindex()  # Has 3 periods
    with pytest.raises(ValueError, match="Vector shape"):
        ListTimeVector(
            timeindex=timeindex,
            vector=np.array([2.0, 3.0], dtype=np.float64),
            unit=None,
            is_max_level=True,
            is_zero_one_profile=None,
        )


def test_init_level():
    vector = ListTimeVector(
        timeindex=_list_timeindex(),
        vector=np.array([2.0, 3.0, 4.0], dtype=np.float32),
        unit="MW",
        is_max_level=True,
        is_zero_one_profile=None,
    )

    assert vector.get_unit() == "MW"
    assert vector.is_max_level() is True
    assert vector.is_zero_one_profile() is None
    assert vector.get_reference_period() is None
    assert vector.get_loader() is None


def test_init_profile():
    vector = ListTimeVector(
        timeindex=_list_timeindex(),
        vector=np.array([2.0, 3.0, 4.0], dtype=np.float32),
        unit="MW",
        is_max_level=None,
        is_zero_one_profile=True,
    )

    assert vector.get_unit() == "MW"
    assert vector.is_max_level() is None
    assert vector.is_zero_one_profile() is True


@pytest.mark.parametrize(
    ("time_index", "vector", "unit", "is_max_level", "is_zero_one_profile", "reference_period", "expected_equal"),
    [
        (_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), None, None, True, None, True),
        (_other_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), None, None, True, None, False),
        (_list_timeindex(), np.array([4.0, 3.0, 2.0], dtype=np.float32), None, None, True, None, False),
        (_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), "MW", None, True, None, False),
        (_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), None, True, None, None, False),
        (_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), None, None, True, ReferencePeriod(start_year=2021, num_years=1), False),
    ],
)
def test_eq_(
    time_index: TimeIndex,
    vector: NDArray,
    unit: str | None,
    is_max_level: bool | None,
    is_zero_one_profile: bool | None,
    reference_period: ReferencePeriod | None,
    expected_equal: bool,
):
    vector1 = ListTimeVector(
        timeindex=_list_timeindex(),
        vector=np.array([2.0, 3.0, 4.0], dtype=np.float32),
        unit=None,
        is_max_level=None,
        is_zero_one_profile=True,
        reference_period=None,
    )
    vector2 = ListTimeVector(
        timeindex=time_index,
        vector=vector,
        unit=unit,
        is_max_level=is_max_level,
        is_zero_one_profile=is_zero_one_profile,
        reference_period=reference_period,
    )

    assert (vector1 == vector2) is expected_equal


@pytest.mark.parametrize(
    ("time_index", "vector", "unit", "is_max_level", "is_zero_one_profile", "reference_period", "expected_equal"),
    [
        (_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), None, None, True, None, True),
        (_other_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), None, None, True, None, False),
        (_list_timeindex(), np.array([4.0, 3.0, 2.0], dtype=np.float32), None, None, True, None, False),
        (_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), "MW", None, True, None, False),
        (_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), None, True, None, None, False),
        (_list_timeindex(), np.array([2.0, 3.0, 4.0], dtype=np.float32), None, None, True, ReferencePeriod(start_year=2021, num_years=1), False),
    ],
)
def test_hash_(
    time_index: TimeIndex,
    vector: NDArray,
    unit: str | None,
    is_max_level: bool | None,
    is_zero_one_profile: bool | None,
    reference_period: ReferencePeriod | None,
    expected_equal: bool,
):
    vector1 = ListTimeVector(
        timeindex=_list_timeindex(),
        vector=np.array([2.0, 3.0, 4.0], dtype=np.float32),
        unit=None,
        is_max_level=None,
        is_zero_one_profile=True,
        reference_period=None,
    )
    vector2 = ListTimeVector(
        timeindex=time_index,
        vector=vector,
        unit=unit,
        is_max_level=is_max_level,
        is_zero_one_profile=is_zero_one_profile,
        reference_period=reference_period,
    )

    assert (hash(vector1) == hash(vector2)) is expected_equal


@pytest.mark.parametrize(
    ("dtype", "expected_vector"),
    [
        (np.float32, np.array([2.0, 3.0, 4.0], dtype=np.float32)),
        (np.float64, np.array([2.0, 3.0, 4.0], dtype=np.float64)),
    ],
)
def test_get_vector(dtype: np.dtype, expected_vector: NDArray):
    vector = ListTimeVector(
        timeindex=_list_timeindex(),
        vector=np.array([2.0, 3.0, 4.0], dtype=dtype),
        unit="MW",
        is_max_level=True,
        is_zero_one_profile=None,
    )

    is_float32 = dtype == np.float32
    result = vector.get_vector(is_float32=is_float32)

    assert np.array_equal(result, expected_vector)

def test_is_constant_returns_false():
    vector = ListTimeVector(
        timeindex=_list_timeindex(),
        vector=np.array([2.0, 3.0, 4.0], dtype=np.float32),
        unit=None,
        is_max_level=True,
        is_zero_one_profile=None,
    )

    assert vector.is_constant() is False

def test_get_loader_returns_none():
    vector = ListTimeVector(
        timeindex=_list_timeindex(),
        vector=np.array([2.0, 3.0, 4.0], dtype=np.float32),
        unit=None,
        is_max_level=True,
        is_zero_one_profile=None,
    )

    assert vector.get_loader() is None
