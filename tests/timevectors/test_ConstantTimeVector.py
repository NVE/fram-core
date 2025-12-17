import numpy as np
import pytest
from numpy.typing import NDArray

from framcore.fingerprints import Fingerprint
from framcore.loaders import TimeVectorLoader
from framcore.timeindexes import ConstantTimeIndex, TimeIndex
from framcore.timevectors import ConstantTimeVector, ReferencePeriod, TimeVector


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
    with pytest.raises(ValueError, match="Invalid input arguments for ConstantTimeVector"):
        ConstantTimeVector(
            scalar=1.0,
            unit="MW",
            is_max_level=is_max_level,
            is_zero_one_profile=is_zero_one_profile,
        )


def test_init_level():
    vector = ConstantTimeVector(
        scalar=1.0,
        unit="MW",
        is_max_level=True,
    )

    assert vector.get_expr_str() is not None
    assert vector.get_unit() == "MW"
    assert vector.is_max_level() is True
    assert vector.is_zero_one_profile() is None


def test_init_profile():
    vector = ConstantTimeVector(
        scalar=1.0,
        unit="MW",
        is_zero_one_profile=True,
    )

    assert vector.get_expr_str() is not None
    assert vector.get_unit() == "MW"
    assert vector.is_max_level() is None
    assert vector.is_zero_one_profile() is True


@pytest.mark.parametrize(
    ("v1_kwargs", "v2_kwargs", "expected_equal"),
    [
        # Same attributes
        (
            {"scalar": 1.0, "unit": "MW", "is_max_level": True},
            {"scalar": 1.0, "unit": "MW", "is_max_level": True},
            True,
        ),
        # Different scalar
        (
            {"scalar": 1.0, "unit": "MW", "is_max_level": True},
            {"scalar": 2.0, "unit": "MW", "is_max_level": True},
            False,
        ),
        # Different unit
        (
            {"scalar": 1.0, "unit": "MW", "is_max_level": True},
            {"scalar": 1.0, "unit": "kW", "is_max_level": True},
            False,
        ),
        # Different is_max_level
        (
            {"scalar": 1.0, "unit": "MW", "is_max_level": True},
            {"scalar": 1.0, "unit": "MW", "is_max_level": False},
            False,
        ),
        # Different is_zero_one_profile
        (
            {"scalar": 1.0, "unit": "MW", "is_zero_one_profile": True},
            {"scalar": 1.0, "unit": "MW", "is_zero_one_profile": False},
            False,
        ),
        # Different reference_period
        (
            {"scalar": 1.0, "unit": "MW", "is_max_level": True, "reference_period": ReferencePeriod(start_year=2020, num_years=1)},
            {"scalar": 1.0, "unit": "MW", "is_max_level": True, "reference_period": ReferencePeriod(start_year=2021, num_years=1)},
            False,
        ),
    ],
)
def test__eq__(v1_kwargs, v2_kwargs, expected_equal):
    v1 = ConstantTimeVector(**v1_kwargs)
    v2 = ConstantTimeVector(**v2_kwargs)
    if expected_equal:
        assert v1 == v2
    else:
        assert v1 != v2


def test_eq_with_non_constanttimevector():  # noqa: C901
    class DummyTimeVector(TimeVector):
        def __eq__(self, other) -> bool:
            pass

        def __hash__(self) -> int:
            pass

        def get_loader(self) -> TimeVectorLoader | None:
            return super().get_loader()

        def get_vector(self, is_float32: bool) -> NDArray:
            return np.array([1.0], dtype=np.float32 if is_float32 else np.float64)

        def get_timeindex(self) -> TimeIndex | None:
            return None

        def is_constant(self) -> bool:
            return False

        def is_max_level(self) -> bool | None:
            return None

        def is_zero_one_profile(self) -> bool | None:
            return None

        def get_unit(self) -> str | None:
            return None

        def get_fingerprint(self) -> Fingerprint:
            return Fingerprint("dummy")

        def get_reference_period(self) -> ReferencePeriod | None:
            return None

    v1 = ConstantTimeVector(scalar=1.0, unit="MW", is_max_level=True)
    assert (v1 == DummyTimeVector()) is False


@pytest.mark.parametrize(
    ("v1_kwargs", "v2_kwargs", "expected_equal_hash"),
    [
        # Equal objects
        ({"scalar": 1.0, "unit": "MW", "is_max_level": True}, {"scalar": 1.0, "unit": "MW", "is_max_level": True}, True),
        # Different scalar
        ({"scalar": 1.0, "unit": "MW", "is_max_level": True}, {"scalar": 2.0, "unit": "MW", "is_max_level": True}, False),
        # Different unit
        ({"scalar": 1.0, "unit": "MW", "is_max_level": True}, {"scalar": 1.0, "unit": "kW", "is_max_level": True}, False),
        # Different is_max_level
        ({"scalar": 1.0, "unit": "MW", "is_max_level": True}, {"scalar": 1.0, "unit": "MW", "is_max_level": False}, False),
        # Different is_zero_one_profile
        ({"scalar": 1.0, "unit": "MW", "is_zero_one_profile": True}, {"scalar": 1.0, "unit": "MW", "is_zero_one_profile": False}, False),
        # Different reference_period
        (
            {"scalar": 1.0, "unit": "MW", "is_max_level": True, "reference_period": ReferencePeriod(start_year=2020, num_years=1)},
            {"scalar": 1.0, "unit": "MW", "is_max_level": True, "reference_period": ReferencePeriod(start_year=2021, num_years=1)},
            False,
        ),
    ],
)
def test_hash_(v1_kwargs, v2_kwargs, expected_equal_hash):
    v1 = ConstantTimeVector(**v1_kwargs)
    v2 = ConstantTimeVector(**v2_kwargs)
    if expected_equal_hash:
        assert hash(v1) == hash(v2)
        assert v1 == v2  # Sanity check
    else:
        assert hash(v1) != hash(v2)


def test_hash_in_set_behavior():
    v1 = ConstantTimeVector(scalar=1.0, unit="MW", is_max_level=True)
    v2 = ConstantTimeVector(scalar=1.0, unit="MW", is_max_level=True)
    v3 = ConstantTimeVector(scalar=2.0, unit="MW", is_max_level=True)
    s = {v1, v3}
    assert v2 in s
    assert ConstantTimeVector(scalar=2.0, unit="MW", is_max_level=True) in s
    assert ConstantTimeVector(scalar=3.0, unit="MW", is_max_level=True) not in s


@pytest.mark.parametrize(
    ("unit", "expected_expr_str"),
    [("MW", "3.5 MW"), (None, "3.5")],
)
def test_expr_str(unit: str | None, expected_expr_str: str):
    vector = ConstantTimeVector(
        scalar=3.5,
        unit=unit,
        is_zero_one_profile=True,
    )
    expr_str = vector.get_expr_str()
    assert expr_str == expected_expr_str


@pytest.mark.parametrize(
    ("scalar", "is_float32", "expected_dtype"),
    [
        (5.0, True, np.float32),
        (5.0, False, np.float64),
    ],
)
def test_get_vector(scalar, is_float32, expected_dtype):
    vector = ConstantTimeVector(
        scalar=scalar,
        unit="MW",
        is_max_level=True,
    )

    arr = vector.get_vector(is_float32=is_float32)

    assert isinstance(arr, np.ndarray)
    assert arr.shape == (1,)
    assert arr.dtype == expected_dtype
    assert arr[0] == scalar


def test_get_timeindex_expectect_constant_timeindex():
    vector = ConstantTimeVector(
        scalar=2.0,
        unit="kW",
        is_zero_one_profile=True,
    )

    timeindex = vector.get_timeindex()

    assert isinstance(timeindex, ConstantTimeIndex)


def test_is_constant_returns_true():
    vector = ConstantTimeVector(
        scalar=10.0,
        unit="kWh",
        is_max_level=True,
    )

    assert vector.is_constant() is True


@pytest.mark.parametrize(
    ("is_max_level", "is_zero_one_profile", "reference_period", "expected_result"),
    [
        (True, None, ReferencePeriod(start_year=2022, num_years=2), ReferencePeriod(start_year=2022, num_years=2)),
        (None, False, None, ConstantTimeIndex().get_reference_period()),
        (None, True, None, None),
        (True, None, None, None),
        (False, None, None, None),
    ],
)
def test_get_reference_period(
    is_max_level: bool | None,
    is_zero_one_profile: bool | None,
    reference_period: ReferencePeriod | None,
    expected_result: ReferencePeriod | None,
):
    vector = ConstantTimeVector(
        scalar=4.0,
        unit="kW",
        is_max_level=is_max_level,
        is_zero_one_profile=is_zero_one_profile,
        reference_period=reference_period,
    )

    returned_ref_period = vector.get_reference_period()

    assert returned_ref_period == expected_result
