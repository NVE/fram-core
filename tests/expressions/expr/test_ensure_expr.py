from unittest.mock import Mock

import pytest

from framcore.curves import LoadedCurve
from framcore.expressions import Expr, ensure_expr
from framcore.loaders import CurveLoader
from framcore.timevectors import ConstantTimeVector, TimeVector


def test_returns_none_with_input_none():
    expected = None
    result = ensure_expr(None)

    assert result == expected


@pytest.mark.parametrize(
    "value",
    [
        "timevector_1",
        ConstantTimeVector(5.0, is_zero_one_profile=False),
        Expr("timevector_1"),
        LoadedCurve(curve_id="curve_1", loader=Mock(CurveLoader)),
    ],
)
def test_when_value_expected_type_result_is_expr(value: str | TimeVector | Expr) -> None:
    is_flow = False
    is_stock = False
    is_level = False
    is_profile = False
    profile = None

    result = ensure_expr(value=value, is_flow=is_flow, is_stock=is_stock, is_level=is_level, is_profile=is_profile, profile=profile)

    assert isinstance(result, Expr)
    if isinstance(value, Expr):
        assert result.get_src() == value.get_src()
    else:
        assert result.get_src() == value
    assert result.is_flow() is is_flow
    assert result.is_stock() is is_stock
    assert result.is_level() is is_level
    assert result.is_profile() is is_profile
    assert result.get_profile() == profile


def test_when_value_is_expr_with_non_matching_type_raises_value_error() -> None:
    input_expr = Expr("timevector_1", is_flow=True, is_level=True)

    match_message = "Given Expr has a mismatch between expected and actual flow/stock or level/profile status:"
    with pytest.raises(ValueError, match=match_message):
        ensure_expr(
            value=input_expr,
            is_flow=False,
            is_stock=False,
            is_level=False,
            is_profile=True,
        )


def test_when_value_is_of_invalid_type_raises_type_error() -> None:
    invalid_value = 42  # type: ignore

    match_message = "Expected value to be of type Expr, str, Curve, TimeVector or None. Got int."
    with pytest.raises(TypeError, match=match_message):
        ensure_expr(value=invalid_value)


def test_when_both_is_level_and_is_profile_are_true_raises_value_error() -> None:
    match_message = "Expr cannot be both level and a profile. Set either is_level or is_profile True or both False."
    with pytest.raises(ValueError, match=match_message):
        ensure_expr(
            value="timevector_1",
            is_level=True,
            is_profile=True,
        )


def test_when_both_is_flow_and_is_stock_are_true_raises_value_error() -> None:
    match_message = "Expr cannot be both flow and stock. Set either is_flow or is_stock True or both False."
    with pytest.raises(ValueError, match=match_message):
        ensure_expr(
            value="timevector_1",
            is_flow=True,
            is_stock=True,
        )


@pytest.mark.parametrize(
    ("is_flow", "is_stock"),
    [
        (True, False),
        (False, True),
    ],
)
def test_when_is_profile_and_flow_or_stock_raise_value_error(is_flow: bool, is_stock: bool) -> None:
    match_message = "Expr cannot be both a profile and a flow/stock. Profiles must be coefficients."
    with pytest.raises(ValueError, match=match_message):
        ensure_expr(
            value="timevector_1",
            is_profile=True,
            is_flow=is_flow,
            is_stock=is_stock,
        )
