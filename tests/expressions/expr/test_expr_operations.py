import operator

import pytest

from framcore.expressions import Expr
from framcore.timevectors import ConstantTimeVector

# | expr1       | operation | expr2       | is_supported

# | level flow  | +         | level flow  | True
# | level flow  | +         | level stock | False
# | level flow  | +         | level none  | False
# | level flow  | +         | none        | False
# | level stock | +         | level stock | True
# | level stock | +         | level flow  | False
# | level stock | +         | level none  | False
# | level stock | +         | none        | False
# | level none  | +         | level none  | True
# | level none  | +         | level flow  | False
# | level none  | +         | level stock | False
# | level none  | +         | none        | False
# | none        | +         | level flow  | False
# | none        | +         | level stock | False
# | none        | +         | level none  | False

# | level flow  | -         | level flow  | False
# | level flow  | -         | level stock | False
# | level flow  | -         | level none  | False
# | level flow  | -         | none        | False
# | level stock | -         | level stock | False
# | level stock | -         | level flow  | False
# | level stock | -         | level none  | False
# | level stock | -         | none        | False
# | level none  | -         | level none  | True
# | level none  | -         | level flow  | False
# | level none  | -         | level stock | False
# | level none  | -         | none        | False
# | none        | -         | level flow  | False
# | none        | -         | level stock | False
# | none        | -         | level none  | False

# | level flow  | *         | level flow  | False
# | level flow  | *         | level stock | False
# | level flow  | *         | level none  | True
# | level flow  | *         | none        | True
# | level stock | *         | level stock | False
# | level stock | *         | level flow  | False
# | level stock | *         | level none  | True
# | level stock | *         | none        | True
# | level none  | *         | level none  | True
# | level none  | *         | level flow  | True
# | level none  | *         | level stock | True
# | level none  | *         | none        | True
# | none        | *         | level flow  | True
# | none        | *         | level stock | True
# | none        | *         | level none  | True

# | level flow  | /         | level flow  | True
# | level flow  | /         | level stock | False
# | level flow  | /         | level none  | True
# | level flow  | /         | none        | True
# | level stock | /         | level stock | True
# | level stock | /         | level flow  | False
# | level stock | /         | level none  | True
# | level stock | /         | none        | True
# | level none  | /         | level none  | True
# | level none  | /         | level flow  | False
# | level none  | /         | level stock | False
# | level none  | /         | none        | True
# | none        | /         | level flow  | False
# | none        | /         | level stock | False
# | none        | /         | level none  | True

# | profile none  | +         | profile none  | True
# | profile none  | +         | none          | False
# | none          | +         | profile none  | False

# | profile none  | -         | profile none  | True
# | profile none  | -         | none          | False
# | none          | -         | profile none  | False

# | profile none  | *         | profile none  | False
# | profile none  | *         | none          | True
# | none          | *         | profile none  | True

# | profile none  | /         | profile none  | False
# | profile none  | /         | none          | True
# | none          | /         | profile none  | True


def _test_supported_expr_operation(expr1: Expr, expr2: Expr, operation: callable) -> None:
    try:
        result_expr = operation(expr1, expr2)
        assert result_expr is not None
    except Exception:
        pytest.fail(f"Unexpected Exception raised for operation '{operation.__name__}' between expr1={expr1} and expr2={expr2}.")


def _test_unsupported_expr_operation(expr1: Expr, expr2: Expr, operation: callable) -> None:
    with pytest.raises(ValueError, match="Unsupported case:"):
        _ = operation(expr1, expr2)


def _constant_time_vector(scalar: float = 1.0, is_zero_one_profile: bool | None = False) -> ConstantTimeVector:
    return ConstantTimeVector(scalar=float(scalar), is_zero_one_profile=is_zero_one_profile, is_max_level=(None if is_zero_one_profile is not None else True))


def _level_expr(scalar: float, is_flow: bool = False, is_stock: bool = False) -> Expr:
    return Expr(
        src=_constant_time_vector(scalar=scalar, is_zero_one_profile=False),
        is_level=True,
        is_flow=is_flow,
        is_stock=is_stock,
    )


def _profile_expr(scalar: float, is_flow: bool = False, is_stock: bool = False) -> Expr:
    return Expr(
        src=_constant_time_vector(scalar=scalar, is_zero_one_profile=True),
        is_profile=True,
        is_flow=is_flow,
        is_stock=is_stock,
    )


def _level_flow_expr(scalar: float) -> Expr:
    return _level_expr(scalar=scalar, is_flow=True)


def _level_stock_expr(scalar: float) -> Expr:
    return _level_expr(scalar=scalar, is_stock=True)


def _level_none_expr(scalar: float) -> Expr:
    return _level_expr(scalar=scalar)


def _profile_flow_expr(scalar: float) -> Expr:
    return _profile_expr(scalar=scalar)


def _profile_stock_expr(scalar: float) -> Expr:
    return _profile_expr(scalar=scalar)


def _profile_none_expr(scalar: float) -> Expr:
    return _profile_expr(scalar=scalar)


def _none_expr(scalar: float) -> Expr:
    return Expr(
        src=_constant_time_vector(scalar=scalar, is_zero_one_profile=False),
    )


@pytest.mark.parametrize(
    ("expr1", "expr2", "is_supported"),
    [
        # level flow + level flow
        (
            _level_flow_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            True,
        ),
        # level flow + level stock
        (
            _level_flow_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level flow + level none
        (
            _level_flow_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            False,
        ),
        # level flow + none
        (
            _level_flow_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            False,
        ),
        # level stock + level stock
        (
            _level_stock_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            True,
        ),
        # level stock + level flow
        (
            _level_stock_expr(scalar=2.0),
            _level_flow_expr(scalar=1.0),
            False,
        ),
        # level stock + level none
        (
            _level_stock_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            False,
        ),
        # level stock + none
        (
            _level_stock_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            False,
        ),
        # level none + level none
        (
            _level_none_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
        # level none + level flow
        (
            _level_none_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # level none + level stock
        (
            _level_none_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level none + none
        (
            _level_none_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            False,
        ),
        # none + level flow
        (
            _none_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # none + level stock
        (
            _none_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # none + level none
        (
            _none_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            False,
        ),
    ],
    ids=[
        "level_flow_+_level_flow",
        "level_flow_+_level_stock",
        "level_flow_+_level_none",
        "level_flow_+_none",
        "level_stock_+_level_stock",
        "level_stock_+_level_flow",
        "level_stock_+_level_none",
        "level_stock_+_none",
        "level_none_+_level_none",
        "level_none_+_level_flow",
        "level_none_+_level_stock",
        "level_none_+_none",
        "none_+_level_flow",
        "none_+_level_stock",
        "none_+_level_none",
    ],
)
def test_add_level_exprs(expr1: Expr, expr2: Expr, is_supported: bool):
    if is_supported:
        _test_supported_expr_operation(expr1, expr2, operator.add)
    else:
        _test_unsupported_expr_operation(expr1, expr2, operator.add)


@pytest.mark.parametrize(
    ("expr1", "expr2", "is_supported"),
    [
        # level flow - level flow
        (
            _level_flow_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # level flow - level stock
        (
            _level_flow_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level flow - level none
        (
            _level_flow_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            False,
        ),
        # level flow - none
        (
            _level_flow_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            False,
        ),
        # level stock - level stock
        (
            _level_stock_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level stock - level flow
        (
            _level_stock_expr(scalar=2.0),
            _level_flow_expr(scalar=1.0),
            False,
        ),
        # level stock - level none
        (
            _level_stock_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            False,
        ),
        # level stock - none
        (
            _level_stock_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            False,
        ),
        # level none - level none
        (
            _level_none_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
        # level none - level flow
        (
            _level_none_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # level none - level stock
        (
            _level_none_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level none - none
        (
            _level_none_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            False,
        ),
        # none - level flow
        (
            _none_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # none - level stock
        (
            _none_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # none - level none
        (
            _none_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            False,
        ),
    ],
    ids=[
        "level_flow_-_level_flow",
        "level_flow_-_level_stock",
        "level_flow_-_level_none",
        "level_flow_-_none",
        "level_stock_-_level_stock",
        "level_stock_-_level_flow",
        "level_stock_-_level_none",
        "level_stock_-_none",
        "level_none_-_level_none",
        "level_none_-_level_flow",
        "level_none_-_level_stock",
        "level_none_-_none",
        "none_-_level_flow",
        "none_-_level_stock",
        "none_-_level_none",
    ],
)
def test_subtract_level_exprs(expr1: Expr, expr2: Expr, is_supported: bool):
    if is_supported:
        _test_supported_expr_operation(expr1, expr2, operator.sub)
    else:
        _test_unsupported_expr_operation(expr1, expr2, operator.sub)


@pytest.mark.parametrize(
    ("expr1", "expr2", "is_supported"),
    [
        # level flow * level flow
        (
            _level_flow_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # level flow * level stock
        (
            _level_flow_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level flow * level none
        (
            _level_flow_expr(scalar=1.0),
            _level_none_expr(scalar=5.0),
            True,
        ),
        # level flow * none
        (
            _level_flow_expr(scalar=1.0),
            _none_expr(scalar=5.0),
            True,
        ),
        # level stock * level stock
        (
            _level_stock_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level stock * level flow
        (
            _level_stock_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # level stock * level none
        (
            _level_stock_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
        # level stock * none
        (
            _level_stock_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            True,
        ),
        # level none * level none
        (
            _level_none_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
        # level none * level flow
        (
            _level_none_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            True,
        ),
        # level none * level stock
        (
            _level_none_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            True,
        ),
        # level none * none
        (
            _level_none_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            True,
        ),
        # none * level flow
        (
            _none_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            True,
        ),
        # none * level stock
        (
            _none_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            True,
        ),
        # none * level none
        (
            _none_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
    ],
    ids=[
        "level_flow_*_level_flow",
        "level_flow_*_level_stock",
        "level_flow_*_level_none",
        "level_flow_*_none",
        "level_stock_*_level_stock",
        "level_stock_*_level_flow",
        "level_stock_*_level_none",
        "level_stock_*_none",
        "level_none_*_level_none",
        "level_none_*_level_flow",
        "level_none_*_level_stock",
        "level_none_*_none",
        "none_*_level_flow",
        "none_*_level_stock",
        "none_*_level_none",
    ],
)
def test_multiply_level_exprs(expr1: Expr, expr2: Expr, is_supported: bool):
    if is_supported:
        _test_supported_expr_operation(expr1, expr2, operator.mul)
    else:
        _test_unsupported_expr_operation(expr1, expr2, operator.mul)


@pytest.mark.parametrize(
    ("expr1", "expr2", "is_supported"),
    [
        # level flow / level flow
        (
            _level_flow_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            True,
        ),
        # level flow / level stock
        (
            _level_flow_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level flow / level none
        (
            _level_flow_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
        # level flow / none
        (
            _level_flow_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            True,
        ),
        # level stock / level stock
        (
            _level_stock_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            True,
        ),
        # level stock / level flow
        (
            _level_stock_expr(scalar=1.0),
            _level_flow_expr(scalar=1.0),
            False,
        ),
        # level stock / level none
        (
            _level_stock_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
        # level stock / none
        (
            _level_stock_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            True,
        ),
        # level none / level none
        (
            _level_none_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
        # level none / level flow
        (
            _level_none_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # level none / level stock
        (
            _level_none_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # level none / none
        (
            _level_none_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            True,
        ),
        # none / level flow
        (
            _none_expr(scalar=1.0),
            _level_flow_expr(scalar=2.0),
            False,
        ),
        # none / level stock
        (
            _none_expr(scalar=1.0),
            _level_stock_expr(scalar=2.0),
            False,
        ),
        # none / level none
        (
            _none_expr(scalar=1.0),
            _level_none_expr(scalar=2.0),
            True,
        ),
    ],
    ids=[
        "level_flow_/_level_flow",
        "level_flow_/_level_stock",
        "level_flow_/_level_none",
        "level_flow_/_none",
        "level_stock_/_level_stock",
        "level_stock_/_level_flow",
        "level_stock_/_level_none",
        "level_stock_/_none",
        "level_none_/_level_none",
        "level_none_/_level_flow",
        "level_none_/_level_stock",
        "level_none_/_none",
        "none_/_level_flow",
        "none_/_level_stock",
        "none_/_level_none",
    ],
)
def test_divide_level_exprs(expr1: Expr, expr2: Expr, is_supported: bool):
    if is_supported:
        _test_supported_expr_operation(expr1, expr2, operator.truediv)
    else:
        _test_unsupported_expr_operation(expr1, expr2, operator.truediv)


@pytest.mark.parametrize(
    ("expr1", "expr2", "is_supported"),
    [
        # profile none + profile none
        (
            _profile_none_expr(scalar=1.0),
            _profile_none_expr(scalar=2.0),
            True,
        ),
        # profile none + none
        (
            _profile_none_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            False,
        ),
        # none + profile none
        (
            _none_expr(scalar=1.0),
            _profile_none_expr(scalar=2.0),
            False,
        ),
    ],
    ids=[
        "profile_none_+_profile_none",
        "profile_none_+_none",
        "none_+_profile_none",
    ],
)
def test_add_profile_exprs(expr1: Expr, expr2: Expr, is_supported: bool):
    if is_supported:
        _test_supported_expr_operation(expr1, expr2, operator.add)
    else:
        _test_unsupported_expr_operation(expr1, expr2, operator.add)


@pytest.mark.parametrize(
    ("expr1", "expr2", "is_supported"),
    [
        # profile none - profile none
        (
            _profile_none_expr(scalar=1.0),
            _profile_none_expr(scalar=2.0),
            True,
        ),
        # profile none - none
        (
            _profile_none_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            False,
        ),
        # none - profile none
        (
            _none_expr(scalar=1.0),
            _profile_none_expr(scalar=2.0),
            False,
        ),
    ],
    ids=[
        "profile_none_-_profile_none",
        "profile_none_-_none",
        "none_-_profile_none",
    ],
)
def test_subtract_profile_exprs(expr1: Expr, expr2: Expr, is_supported: bool):
    if is_supported:
        _test_supported_expr_operation(expr1, expr2, operator.sub)
    else:
        _test_unsupported_expr_operation(expr1, expr2, operator.sub)


@pytest.mark.parametrize(
    ("expr1", "expr2", "is_supported"),
    [
        # profile none * profile none
        (
            _profile_none_expr(scalar=1.0),
            _profile_none_expr(scalar=2.0),
            False,
        ),
        # profile none * none
        (
            _profile_none_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            True,
        ),
        # none * profile none
        (
            _none_expr(scalar=1.0),
            _profile_none_expr(scalar=2.0),
            True,
        ),
    ],
    ids=[
        "profile_none_*_profile_none",
        "profile_none_*_none",
        "none_*_profile_none",
    ],
)
def test_multiply_profile_exprs(expr1: Expr, expr2: Expr, is_supported: bool):
    if is_supported:
        _test_supported_expr_operation(expr1, expr2, operator.mul)
    else:
        _test_unsupported_expr_operation(expr1, expr2, operator.mul)


@pytest.mark.parametrize(
    ("expr1", "expr2", "is_supported"),
    [
        # profile none / profile none
        (
            _profile_none_expr(scalar=1.0),
            _profile_none_expr(scalar=2.0),
            False,
        ),
        # profile none / none
        (
            _profile_none_expr(scalar=1.0),
            _none_expr(scalar=2.0),
            True,
        ),
        # none / profile none
        (
            _none_expr(scalar=1.0),
            _profile_none_expr(scalar=2.0),
            True,
        ),
    ],
    ids=[
        "profile_none_/_profile_none",
        "profile_none_/_none",
        "none_/_profile_none",
    ],
)
def test_divide_profile_exprs(expr1: Expr, expr2: Expr, is_supported: bool):
    if is_supported:
        _test_supported_expr_operation(expr1, expr2, operator.truediv)
    else:
        _test_unsupported_expr_operation(expr1, expr2, operator.truediv)


@pytest.mark.parametrize(
    "operation",
    [
        operator.add,
        operator.sub,
        operator.mul,
        operator.truediv,
    ],
)
def test_none_operations(operation):
    expr1 = _none_expr(scalar=1.0)
    expr2 = _none_expr(scalar=2.0)

    result = operation(expr1, expr2)

    assert result is not None


@pytest.mark.parametrize(
    ("expr1", "expr2", "operation", "expected_value"),
    [
        (_level_flow_expr(scalar=1.0), _level_flow_expr(scalar=2.0), operator.add, 3.0),
        (_profile_none_expr(scalar=1.0), _profile_none_expr(scalar=2.0), operator.add, 3.0),
        (_level_none_expr(scalar=2.0), _level_none_expr(scalar=1.0), operator.sub, 1.0),
        (_profile_none_expr(scalar=2.0), _profile_none_expr(scalar=1.0), operator.sub, 1.0),
        (_level_none_expr(scalar=2.0), _level_none_expr(scalar=4.0), operator.mul, 8.0),
        (_level_flow_expr(scalar=10.0), _level_flow_expr(scalar=2.0), operator.truediv, 5.0),
    ],
    ids=[
        "level_flow_+_level_flow",
        "profile_none_+_profile_none",
        "level_flow_-_level_flow",
        "profile_none_-_profile_none",
        "level_flow_*_level_none",
        "level_flow_/_level_flow",
    ],
)
def test_operations_with_combinable_constant_timevector_exprs_return_combined_result(
    expr1: Expr, expr2: Expr, operation: callable, expected_value: float,
) -> None:
    result_expr: Expr = operation(expr1, expr2)

    assert result_expr.is_flow() is expr1.is_flow()
    assert result_expr.is_stock() is expr1.is_stock()
    assert result_expr.is_level() is expr1.is_level()
    assert result_expr.is_profile() is expr1.is_profile()

    assert result_expr.get_operations(expect_ops=False, copy_list=False) == ("", [])
    assert result_expr.get_src().get_vector(is_float32=True)[0] == expected_value


@pytest.mark.parametrize(
    ("expr1", "expr2", "operation", "expected_op"),
    [
        # non-combinable profile time vector exprs
        (
            Expr(src=_constant_time_vector(scalar=1.0, is_zero_one_profile=False)),
            Expr(src=_constant_time_vector(scalar=2.0, is_zero_one_profile=True)),
            operator.add,
            "+",
        ),
        # combinable level time vector, non-combinable exprs
        (
            Expr(src=_constant_time_vector(scalar=1.0, is_zero_one_profile=None), is_level=True, profile=None),
            Expr(
                src=_constant_time_vector(scalar=2.0, is_zero_one_profile=None),
                is_level=True,
                profile=Expr(src=_constant_time_vector(scalar=1.0, is_zero_one_profile=True)),
            ),
            operator.mul,
            "*",
        ),
        # uncombinable time vectors within combinable level flow exprs
        (
            Expr(src=_constant_time_vector(scalar=4.0, is_zero_one_profile=True), is_level=True, is_flow=True),
            Expr(src=_constant_time_vector(scalar=2.0, is_zero_one_profile=False), is_level=True, is_flow=True),
            operator.truediv,
            "/",
        ),
    ],
    ids=[
        "non-combinable_profile_time_vector_exprs",
        "combinable_time_vector_non_combinable_exprs",
        "non_combinable_time_vectors_within_combinable_level_flow_exprs",
    ],
)
def test_operations_with_non_combinable_exprs_return_operation_expr(expr1: Expr, expr2: Expr, operation: callable, expected_op: str) -> None:
    result_expr: Expr = operation(expr1, expr2)

    ops, args = result_expr.get_operations(expect_ops=True, copy_list=False)
    assert ops == expected_op
    assert args == [expr1, expr2]


def test_multiple_add_operations_with_uncombinable_exprs_return_chained_operation_expr() -> None:
    expr1 = Expr(src=_constant_time_vector(scalar=1.0, is_zero_one_profile=False))
    expr2 = Expr(src=_constant_time_vector(scalar=1.0, is_zero_one_profile=True))
    expr3 = Expr(src=_constant_time_vector(scalar=3.0, is_zero_one_profile=False))

    intermediate_expr = operator.add(expr1, expr2)
    final_expr = operator.add(intermediate_expr, expr3)

    ops, args = final_expr.get_operations(expect_ops=True, copy_list=False)
    assert ops == "++"
    assert args == [expr1, expr2, expr3]


def test_multiple_operations_with_uncombinable_exprs_and_operations_return_expr_hierarchy() -> None:
    expr1 = Expr(src=_constant_time_vector(scalar=4.0, is_zero_one_profile=False))
    expr2 = Expr(src=_constant_time_vector(scalar=2.0, is_zero_one_profile=True))
    expr3 = Expr(src=_constant_time_vector(scalar=3.0, is_zero_one_profile=False))

    intermediate_expr = operator.sub(expr1, expr2)
    final_expr = operator.mul(intermediate_expr, expr3)

    assert final_expr.get_src() is None  # because it's an operation expression
    ops, args = final_expr.get_operations(expect_ops=True, copy_list=False)
    assert ops == "*"
    assert isinstance(args[0], Expr)
    assert args[0].get_operations(expect_ops=True, copy_list=False)[0] == "-"
    assert args[0].get_operations(expect_ops=True, copy_list=False)[1] == [expr1, expr2]
    assert args[1] == expr3


@pytest.mark.parametrize(
    ("a_number", "operation", "expected_op"),
    [
        (2.0, operator.mul, "*"),
        (2.0, operator.truediv, "/"),
        (2, operator.mul, "*"),
        (2, operator.truediv, "/"),
    ],
)
def test_supported_operations_with_exprs_and_numbers(a_number: float | int, operation: callable, expected_op: str) -> None:
    expr = _level_flow_expr(scalar=3.0)

    result = operation(expr, a_number)

    assert result.get_src() is None
    assert result.get_operations(expect_ops=True, copy_list=False)[0] == expected_op
    assert result.get_operations(expect_ops=True, copy_list=False)[1][0] == expr
    assert isinstance(result.get_operations(expect_ops=True, copy_list=False)[1][1], Expr)


@pytest.mark.parametrize(
    ("a_number", "operation"),
    [
        (2.0, operator.add),
        (2.0, operator.sub),
    ],
)
def test_unsupported_operations_with_exprs_and_numbers_raise_value_error(a_number: float | int, operation: callable):
    expr = _level_flow_expr(scalar=3.0)
    with pytest.raises(ValueError, match="Only support multiplication and division with numbers"):
        operation(expr, a_number)


@pytest.mark.parametrize(
    ("unsupported_value", "operation"),
    [
        ("a string", operator.add),
        ("a_string", operator.sub),
        ("a_string", operator.mul),
        ("a_string", operator.truediv),
    ],
)
def test_operation_with_non_supported_types_raise_type_error(unsupported_value, operation: callable):
    expr = _level_flow_expr(scalar=3.0)
    with pytest.raises(TypeError, match="Only support Expr, int, float. Got unsupported type"):
        operation(expr, unsupported_value)
