from unittest.mock import Mock, patch

import numpy as np
import pytest

from framcore.attributes.level_profile_attributes import LevelProfile, MaxFlowVolume, StockVolume
from framcore.expressions import Expr
from framcore.loaders.loaders import ReferencePeriod
from framcore.querydbs import QueryDB
from framcore.timeindexes.ConstantTimeIndex import SinglePeriodTimeIndex
from framcore.timeindexes.FixedFrequencyTimeIndex import FixedFrequencyTimeIndex
from framcore.timevectors import ConstantTimeVector


class DummyLevelProfile(LevelProfile):
    _IS_ABSTRACT = False


def _level() -> Expr:
    return Expr(
        src=ConstantTimeVector(
            scalar=100.0,
            unit="MWh",
            is_max_level=False,
            is_zero_one_profile=None,
            reference_period=None,
        ),
        is_level=True,
        is_stock=True,
    )


def _level_shift() -> Expr:
    return Expr(
        src=ConstantTimeVector(
            scalar=10.0,
            unit="MWh",
            is_max_level=False,
            is_zero_one_profile=None,
            reference_period=None,
        ),
        is_level=True,
        is_stock=True,
    )


def scale() -> Expr:
    return Expr(
        src=ConstantTimeVector(
            scalar=1.2,
            unit="",
            is_max_level=False,
            is_zero_one_profile=None,
            reference_period=None,
        ),
        is_level=True,
        is_stock=False,
    )


def _intercept() -> Expr:
    return Expr(
        src=ConstantTimeVector(
            scalar=10.0,
            unit="MWh",
            is_max_level=False,
            is_zero_one_profile=None,
            reference_period=None,
        ),
        is_level=True,
        is_stock=True,
    )


def test_get_level_when_level_is_none():
    level_profile = DummyLevelProfile()

    result = level_profile.get_level()

    assert result is None


def test_get_level_when_level_and_level_shift_is_not_none():
    level_profile = StockVolume(level=_level(), level_shift=_level_shift())

    result = level_profile.get_level()

    assert result is not None

    vector = result.get_src()
    assert isinstance(vector, ConstantTimeVector)
    assert vector.get_vector(is_float32=False)[0] == 110.0


def test_get_level_when_scale_is_not_none_expect_expr_with_multiplication_operation():
    level_profile = StockVolume(level=_level(), scale=scale())

    result = level_profile.get_level()

    assert result is not None

    assert result.get_operations(expect_ops=True, copy_list=True)[0] == "*"
    assert scale() in result.get_operations(expect_ops=True, copy_list=True)[1]

@pytest.mark.skip(reason="Skiping until fixed")
def test_get_level_when_level_level_shift_and_scale_is_not_none():
    stock_volume = StockVolume(level=_level(), level_shift=_level_shift(), scale=Expr(src=ConstantTimeVector(scalar=1.2, is_max_level=False)))

    result = stock_volume.get_level()

    assert result is not None

    vector = result.get_src()
    assert isinstance(vector, ConstantTimeVector), "Expected Expr.src to be ConstantTimeVector."
    assert vector.get_vector(is_float32=False)[0] == 132.0


def test_get_intercept_when_scale_is_not_none_should_return_intercept_multiplied_with_scale():
    level_profile = StockVolume(level_shift=_level_shift(), scale=scale(), intercept=_intercept())

    result = level_profile.get_intercept()

    assert result is not None
    assert result.get_operations(expect_ops=True, copy_list=True)[0] == "*"
    assert scale() in result.get_operations(expect_ops=True, copy_list=True)[1]


def test_shift_intercept_when_intercept_is_none():
    level_profile = StockVolume()

    level_profile.shift_intercept(value=10.0, unit="MWh")

    assert isinstance(level_profile.get_intercept(), Expr)
    assert level_profile.get_intercept().get_src().get_vector(is_float32=False)[0] == 10.0


def test_shift_intercept_when_intercept_is_not_none():
    level_profile = StockVolume(intercept=_intercept())

    level_profile.shift_intercept(value=5.0, unit="MWh")

    assert isinstance(level_profile.get_intercept(), Expr)
    assert level_profile.get_intercept().get_src().get_vector(is_float32=False)[0] == 15.0


def test_shift_level_when_shift_level_is_none():
    level_profile = StockVolume(level=_level())

    level_profile.shift_level(value=20.0, unit="MWh", is_max_level=False)

    level = level_profile.get_level()
    assert isinstance(level, Expr)
    assert isinstance(level.get_src(), ConstantTimeVector)
    assert level.get_src().get_vector(is_float32=False)[0] == 120.0


def test_shift_level_when_shift_level_is_not_none():
    level_profile = StockVolume(level=_level(), level_shift=_level_shift())

    level_profile.shift_level(value=20.0, unit="MWh", is_max_level=False)

    level = level_profile.get_level()
    assert isinstance(level, Expr)
    assert isinstance(level.get_src(), ConstantTimeVector)
    assert level.get_src().get_vector(is_float32=False)[0] == 130.0


def test_scale_when_scale_is_none():
    level_profile = StockVolume(level=_level())

    level_profile.scale(value=2.0)

    assert level_profile._scale is not None
    assert isinstance(level_profile._scale, Expr)


def test_scale_when_scale_is_not_none():
    level_profile = StockVolume(level=_level(), scale=scale())

    level_profile.scale(value=2.0)

    assert level_profile._scale is not None
    assert isinstance(level_profile._scale, Expr)
    assert level_profile._scale.get_operations(expect_ops=True, copy_list=True)[0] == "*"


def test_ensure_level_expression_when_level_is_expr():
    level_profile = StockVolume()

    result = level_profile._ensure_level_expr(level=_level())

    assert result is not None
    assert isinstance(result, Expr)
    assert result == _level()


def test_ensure_level_expression_when_level_is_str():
    level_profile = StockVolume()

    result = level_profile._ensure_level_expr(level="level")

    assert result is not None
    assert isinstance(result, Expr)
    assert result.get_src() == "level"
    assert result.is_flow() == level_profile.is_flow()
    assert result.is_stock() == level_profile.is_stock()
    assert result.is_level() is True
    assert result.is_profile() is False
    assert result.get_profile() is None


def test_ensure_level_expression_when_level_is_time_vector():
    level_time_vector = ConstantTimeVector(
        scalar=100.0,
        unit="MWh",
        is_max_level=False,
        is_zero_one_profile=None,
        reference_period=None,
    )
    level_profile = StockVolume()

    result = level_profile._ensure_level_expr(level=level_time_vector)

    assert result is not None
    assert isinstance(result, Expr)
    assert result.get_src() == level_time_vector
    assert result.is_flow() == level_profile.is_flow()
    assert result.is_stock() == level_profile.is_stock()
    assert result.is_level() is True
    assert result.is_profile() is False


def test_ensure_level_expression_when_level_is_none():
    level_profile = StockVolume()

    result = level_profile._ensure_level_expr(level=None)

    assert result is None


def test_ensure_level_expression_when_value_is_not_none():
    level_profile = StockVolume()
    value = 50.0
    unit = "MWh"
    reference_period = ReferencePeriod(start_year=2020, num_years=1)

    result = level_profile._ensure_level_expr(value=value, unit=unit, reference_period=reference_period, level=None)

    assert result is not None
    assert isinstance(result, Expr)
    vector = result.get_src()
    assert isinstance(vector, ConstantTimeVector)
    assert vector.get_vector(is_float32=False)[0] == value
    assert vector.get_unit() == unit
    assert vector.is_zero_one_profile() is None
    assert vector.get_reference_period() == reference_period


def test_ensure_profile_expression_when_profile_is_expr():
    level_profile = MaxFlowVolume()
    time_vector = ConstantTimeVector(
        scalar=100.0,
        unit="MWh",
        is_max_level=False,
        is_zero_one_profile=None,
        reference_period=None,
    )

    result = level_profile._ensure_profile_expr(value=Expr(src=time_vector, is_profile=True))

    assert result is not None
    assert isinstance(result, Expr)
    assert result.get_src() == time_vector


def test_ensure_profile_expression_when_profile_is_str():
    level_profile = MaxFlowVolume()

    result = level_profile._ensure_profile_expr(value="profile")

    assert result is not None
    assert isinstance(result, Expr)
    assert result.get_src() == "profile"
    assert result.is_flow() is False
    assert result.is_stock() is False
    assert result.is_level() is False
    assert result.is_profile() is True
    assert result.get_profile() is None


def test_ensure_profile_expression_when_profile_is_time_vector():
    level_profile = MaxFlowVolume()
    time_vector = ConstantTimeVector(
        scalar=100.0,
        unit="MWh",
        is_max_level=False,
        is_zero_one_profile=None,
        reference_period=None,
    )

    result = level_profile._ensure_profile_expr(value=time_vector)

    assert result is not None
    assert isinstance(result, Expr)
    assert result.get_src() == time_vector
    assert result.is_flow() is False
    assert result.is_stock() is False
    assert result.is_level() is False
    assert result.is_profile() is True
    assert result.get_profile() is None


def test_ensure_profile_expression_when_profile_is_none():
    level_profile = MaxFlowVolume()

    result = level_profile._ensure_profile_expr(value=None)

    assert result is None


def test_get_data_value_returns_level_value_when_intercept_is_none():
    db = Mock(spec=QueryDB)
    scenario_horizon = Mock(spec=FixedFrequencyTimeIndex)
    level_period = Mock(spec=SinglePeriodTimeIndex)

    level_profile = StockVolume(level=_level())

    with (
        patch("framcore.attributes.level_profile_attributes.get_level_value", return_value=10.0),
    ):
        result = level_profile._get_data_value(
            db=db,
            scenario_horizon=scenario_horizon,
            level_period=level_period,
            unit="MWh",
            is_max_level=True,
        )

    assert result == 10.0


def test_get_data_value_returns_sum_of_level_and_intercept():
    db = Mock(spec=QueryDB)
    scenario_horizon = Mock(spec=FixedFrequencyTimeIndex)
    level_period = Mock(spec=SinglePeriodTimeIndex)

    level_profile = StockVolume(level=_level(), intercept=_intercept())

    with (
        patch("framcore.attributes.level_profile_attributes.get_level_value", return_value=10.0),
        patch("framcore.attributes.level_profile_attributes._get_constant_from_expr", return_value=5.0),
    ):
        result = level_profile._get_data_value(
            db=db,
            scenario_horizon=scenario_horizon,
            level_period=level_period,
            unit="MWh",
            is_max_level=True,
        )
    assert result == 15.0


def test_get_data_value_raises_value_error_when_level_is_none():
    level_profile = StockVolume(level=None)
    db = Mock(spec=QueryDB)
    scenario_horizon = Mock(spec=FixedFrequencyTimeIndex)
    level_period = Mock(spec=SinglePeriodTimeIndex)

    with pytest.raises(ValueError, match="Attribute level Expr is None"):
        level_profile._get_data_value(
            db=db,
            scenario_horizon=scenario_horizon,
            level_period=level_period,
            unit="MWh",
            is_max_level=True,
        )


def test_get_scenario_vector_with_profile_none_returns_level_value_times_ones():
    db = Mock(spec=QueryDB)
    scenario_horizon = Mock(spec=FixedFrequencyTimeIndex)
    level_period = Mock(spec=SinglePeriodTimeIndex)
    level_profile = StockVolume(level=Mock(spec=ConstantTimeVector))

    scenario_horizon.get_num_periods.return_value = 3

    with patch("framcore.attributes.level_profile_attributes.get_level_value", return_value=2.0):
        result = level_profile._get_scenario_vector(
            db=db,
            scenario_horizon=scenario_horizon,
            level_period=level_period,
            unit="MWh",
            is_float32=True,
        )

    expected = np.array([2.0, 2.0, 2.0], dtype=np.float32)
    assert np.equal(result, expected).all()


def test_get_scenario_vector_with_profile_returns_level_times_profile_vector():
    db = Mock(spec=QueryDB)
    scenario_horizon = Mock(spec=FixedFrequencyTimeIndex)
    level_period = Mock(spec=SinglePeriodTimeIndex)
    level_profile = StockVolume(level=_level(), profile=Mock(spec=ConstantTimeVector))
    level_profile._profile = level_profile._profile

    with (
        patch("framcore.attributes.level_profile_attributes.get_level_value", return_value=3.0),
        patch("framcore.attributes.level_profile_attributes.get_profile_vector", return_value=np.array([1.0, 2.0, 3.0], dtype=np.float32)),
    ):
        result = level_profile._get_scenario_vector(
            db=db,
            scenario_horizon=scenario_horizon,
            level_period=level_period,
            unit="MWh",
            is_float32=False,
        )

    expected = np.array([3.0, 6.0, 9.0], dtype=np.float32)
    assert np.equal(result, expected).all()


def test_get_scenario_vector_with_intercept_adds_intercept_to_result():
    db = Mock(spec=QueryDB)
    scenario_horizon = Mock(spec=FixedFrequencyTimeIndex)
    level_period = Mock(spec=SinglePeriodTimeIndex)
    level_profile = StockVolume(level=Mock(spec=ConstantTimeVector), intercept=Mock(spec=Expr), profile=Mock(spec=ConstantTimeVector))

    with (
        patch("framcore.attributes.level_profile_attributes.get_level_value", return_value=2.0),
        patch("framcore.attributes.level_profile_attributes.get_profile_vector", return_value=np.array([1.0, 2.0, 3.0], dtype=np.float32)),
        patch("framcore.attributes.level_profile_attributes._get_constant_from_expr", return_value=2.0),
    ):
        result = level_profile._get_scenario_vector(
            db=db,
            scenario_horizon=scenario_horizon,
            level_period=level_period,
            unit="MWh",
            is_float32=True,
        )

    expected = np.array([4.0, 6.0, 8.0], dtype=np.float32)
    assert np.equal(result, expected).all()


def test_get_scenario_vector_raises_value_error_when_level_is_none():
    db = Mock(spec=QueryDB)
    scenario_horizon = Mock(spec=FixedFrequencyTimeIndex)
    level_period = Mock(spec=SinglePeriodTimeIndex)
    level_profile = StockVolume(level=None)

    with pytest.raises(ValueError, match="Attribute level Expr is None"):
        level_profile._get_scenario_vector(
            db=db,
            scenario_horizon=scenario_horizon,
            level_period=level_period,
            unit="MWh",
            is_float32=True,
        )


def test_hash_identical_level_profiles_should_have_same_hash():
    level_profile1 = StockVolume(
        level=_level(),
        profile=None,
        level_shift=_level_shift(),
        intercept=_intercept(),
        scale=scale(),
    )
    level_profile2 = StockVolume(
        level=_level(),
        profile=None,
        level_shift=_level_shift(),
        intercept=_intercept(),
        scale=scale(),
    )
    assert hash(level_profile1) == hash(level_profile2)
    assert level_profile1 == level_profile2


def test_hash_different_level_profiles_should_have_different_hashes():
    level_profile1 = StockVolume(
        level=_level(),
        profile=None,
        level_shift=_level_shift(),
        intercept=_intercept(),
        scale=scale(),
    )
    level_profile2 = StockVolume(
        level=_level(),
        profile=None,
        level_shift=None,  # Different field
        intercept=_intercept(),
        scale=scale(),
    )
    assert hash(level_profile1) != hash(level_profile2)
    assert level_profile1 != level_profile2


def test_hash_changes_with_field_modification():
    level_profile = StockVolume(
        level=_level(),
        profile=None,
        level_shift=_level_shift(),
        intercept=_intercept(),
        scale=scale(),
    )
    original_hash = hash(level_profile)
    level_profile._scale = None
    new_hash = hash(level_profile)
    assert original_hash != new_hash
