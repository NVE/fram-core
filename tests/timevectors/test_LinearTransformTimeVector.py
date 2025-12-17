from datetime import datetime

import numpy as np
import pytest
from numpy.typing import NDArray

from framcore.timeindexes import ListTimeIndex, TimeIndex
from framcore.timevectors import ConstantTimeVector, LinearTransformTimeVector, ListTimeVector, ReferencePeriod, TimeVector


def _constant_timevector() -> ConstantTimeVector:
    return ConstantTimeVector(
        scalar=1.0,
        unit="MW",
        is_max_level=True,
    )


def _list_timeindex() -> ListTimeIndex:
    return ListTimeIndex(
        datetime_list=[
            datetime.fromisocalendar(2021, 1, 1),
            datetime.fromisocalendar(2021, 1, 2),
            datetime.fromisocalendar(2021, 1, 3),
            datetime.fromisocalendar(2021, 1, 4),
        ],
        is_52_week_years=False,
        extrapolate_first_point=False,
        extrapolate_last_point=False,
    )


def _list_timevector(time_index: TimeIndex | None = None) -> ListTimeVector:
    return ListTimeVector(
        timeindex=time_index if time_index is not None else _list_timeindex(),
        vector=np.array([2.0, 3.0, 4.0], dtype=np.float64),
        unit=None,
        is_max_level=True,
        is_zero_one_profile=None,
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
    with pytest.raises(ValueError, match="Invalid input arguments for LinearTransformTimeVector"):
        LinearTransformTimeVector(
            timevector=_constant_timevector(),
            scale=2.0,
            shift=1.0,
            unit=None,
            is_max_level=is_max_level,
            is_zero_one_profile=is_zero_one_profile,
        )


def test_init_level():
    vector = LinearTransformTimeVector(
        timevector=_constant_timevector(),
        scale=2.0,
        shift=1.0,
        unit="MW",
        is_max_level=True,
        is_zero_one_profile=None,
    )

    assert vector.get_unit() == "MW"
    assert vector.is_max_level() is True
    assert vector.is_zero_one_profile() is None
    assert vector.get_unit() == "MW"
    assert vector.get_reference_period() is None
    assert vector.get_loader() is None


def test_init_profile():
    vector = LinearTransformTimeVector(
        timevector=_constant_timevector(),
        scale=2.0,
        shift=1.0,
        unit="MW",
        is_max_level=None,
        is_zero_one_profile=True,
    )

    assert vector.get_unit() == "MW"
    assert vector.is_max_level() is None
    assert vector.is_zero_one_profile() is True


@pytest.mark.parametrize(
    ("scale", "shift", "expected_vector"),
    [
        (1.0, 0.0, np.array([2.0, 3.0, 4.0], dtype=np.float64)),
        (2.0, 0.0, np.array([4.0, 6.0, 8.0], dtype=np.float64)),
        (1.0, 1.0, np.array([3.0, 4.0, 5.0], dtype=np.float64)),
        (2.0, 1.0, np.array([5.0, 7.0, 9.0], dtype=np.float64)),
    ],
)
def test_get_vector(scale: float, shift: float, expected_vector: NDArray):
    base_vector = _list_timevector()

    vector = LinearTransformTimeVector(
        timevector=base_vector,
        scale=scale,
        shift=shift,
        unit=None,
        is_max_level=True,
    )

    result = vector.get_vector(is_float32=False)

    assert result.shape == expected_vector.shape
    assert result.dtype == expected_vector.dtype
    assert np.array_equal(result, expected_vector)


def test_get_timeindex_returns_index_from_timevector():
    base_vector = _list_timevector()

    vector = LinearTransformTimeVector(
        timevector=base_vector,
        scale=1.0,
        shift=0.0,
        unit=None,
        is_max_level=True,
    )

    result_index = vector.get_timeindex()

    expected_index = _list_timeindex()
    assert result_index == expected_index


def test_is_constant_returns_value_from_timevector():
    base_vector = _list_timevector()

    vector = LinearTransformTimeVector(
        timevector=base_vector,
        scale=1.0,
        shift=0.0,
        unit=None,
        is_max_level=True,
    )

    assert vector.is_constant() is base_vector.is_constant()


@pytest.mark.parametrize(
    ("time_vector", "scale", "shift", "unit", "is_max_level", "is_zero_one_profile", "reference_period", "expected_equal"),
    [
        (_list_timevector(), 1.0, 0.0, None, True, None, None, True),
        (_constant_timevector(), 1.0, 0.0, None, True, None, None, False),
        (_list_timevector(), 2.0, 0.0, None, True, None, None, False),
        (_list_timevector(), 1.0, 1.0, None, True, None, None, False),
        (_list_timevector(), 1.0, 0.0, "MW", True, None, None, False),
        (_list_timevector(), 1.0, 0.0, None, None, True, None, False),
        (_list_timevector(), 1.0, 0.0, None, True, None, ReferencePeriod(start_year=2021, num_years=1), False),
    ],
)
def test_eq_(
    time_vector: TimeVector | None,
    scale: float,
    shift: float,
    unit: str | None,
    is_max_level: bool | None,
    is_zero_one_profile: bool | None,
    reference_period: ReferencePeriod | str | None,
    expected_equal: bool,
):
    vector1 = LinearTransformTimeVector(
        timevector=_list_timevector(),
        scale=1.0,
        shift=0.0,
        unit=None,
        is_max_level=True,
        is_zero_one_profile=None,
        reference_period=None,
    )
    vector2 = LinearTransformTimeVector(
        timevector=time_vector,
        scale=scale,
        shift=shift,
        unit=unit,
        is_max_level=is_max_level,
        is_zero_one_profile=is_zero_one_profile,
        reference_period=reference_period,
    )

    assert (vector1 == vector2) is expected_equal


def test_eq_with_different_type():
    base_vector = _list_timevector()
    vector = LinearTransformTimeVector(
        timevector=base_vector,
        scale=2.0,
        shift=1.0,
        unit="MW",
        is_max_level=True,
        is_zero_one_profile=None,
    )
    assert vector != _constant_timevector()

@pytest.mark.parametrize(
    ("time_vector", "scale", "shift", "unit", "is_max_level", "is_zero_one_profile", "reference_period", "expected_equal"),
    [
        (_list_timevector(), 1.0, 0.0, None, True, None, None, True),
        (_constant_timevector(), 1.0, 0.0, None, True, None, None, False),
        (_list_timevector(), 2.0, 0.0, None, True, None, None, False),
        (_list_timevector(), 1.0, 1.0, None, True, None, None, False),
        (_list_timevector(), 1.0, 0.0, "MW", True, None, None, False),
        (_list_timevector(), 1.0, 0.0, None, None, True, None, False),
        (_list_timevector(), 1.0, 0.0, None, True, None, ReferencePeriod(start_year=2021, num_years=1), False),
    ],
)
def test_hash_(
    time_vector: TimeVector | None,
    scale: float,
    shift: float,
    unit: str | None,
    is_max_level: bool | None,
    is_zero_one_profile: bool | None,
    reference_period: ReferencePeriod | str | None,
    expected_equal: bool,
):
    vector1 = LinearTransformTimeVector(
        timevector=_list_timevector(),
        scale=1.0,
        shift=0.0,
        unit=None,
        is_max_level=True,
        is_zero_one_profile=None,
        reference_period=None,
    )
    vector2 = LinearTransformTimeVector(
        timevector=time_vector,
        scale=scale,
        shift=shift,
        unit=unit,
        is_max_level=is_max_level,
        is_zero_one_profile=is_zero_one_profile,
        reference_period=reference_period,
    )

    assert (hash(vector1) == hash(vector2)) is expected_equal
