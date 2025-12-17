from unittest.mock import Mock

import pytest

from framcore.curves import Curve, LoadedCurve
from framcore.expressions import Expr
from framcore.loaders import CurveLoader, TimeVectorLoader
from framcore.timevectors import ConstantTimeVector, LoadedTimeVector


def _profile_expr() -> Expr:
    return Expr(src="time_vector1", is_profile=True)


def _level_expr() -> Expr:
    return Expr(src="time_vector2", is_stock=True, is_level=True)


def test_set_profile_when_expr_is_not_level_raises_value_error():
    expr = _profile_expr()

    with pytest.raises(ValueError, match="Cannot set profile on Expr that is not a level."):
        expr.set_profile(profile=_profile_expr())


def test_set_profile_when_expr_is_level():
    expr = _level_expr()

    expr.set_profile(profile=_profile_expr())

    assert expr.get_profile() == _profile_expr()


def test_verify_operations_when_no_operations_should_not_expect_operations():
    expr = Expr(src=ConstantTimeVector(1.0, is_zero_one_profile=False), is_profile=True)

    try:
        expr._verify_operations(expect_ops=False)
    except Exception as e:
        pytest.fail(f"Expr._verify_operations raised an exception unexpectedly! Expr: {expr}, Operation: None, Exception: {e}")


@pytest.mark.parametrize(
    "operations",
    [
        "+*",
        "+/",
        "-/",
        "-*",
    ],
)
def test_verify_operations_when_expression_contains_illegal_operations_combination_should_raise_exception(operations: str):
    expr = Expr(
        is_profile=True,
        operations=(
            operations,
            [
                Expr(src=ConstantTimeVector(1.0, is_zero_one_profile=False), is_profile=True),
                Expr(src=ConstantTimeVector(2.0, is_zero_one_profile=False), is_profile=True),
                Expr(src=ConstantTimeVector(3.0, is_zero_one_profile=False), is_profile=True),
            ],
        ),
    )

    with pytest.raises(ValueError, match=r"^Found \+- in same operation level as \*/ in operations"):
        expr._verify_operations(expect_ops=True)


@pytest.mark.parametrize(
    ("operations", "expressions"),
    [
        (
            "/*",
            [
                Expr(src=ConstantTimeVector(1.0, is_zero_one_profile=False), is_profile=True),
                Expr(src=ConstantTimeVector(2.0, is_zero_one_profile=False), is_profile=True),
                Expr(src=ConstantTimeVector(3.0, is_zero_one_profile=False), is_profile=True),
            ],
        ),
        (
            "*/*",
            [
                Expr(src=ConstantTimeVector(1.0, is_zero_one_profile=False), is_profile=True),
                Expr(src=ConstantTimeVector(2.0, is_zero_one_profile=False), is_profile=True),
                Expr(src=ConstantTimeVector(3.0, is_zero_one_profile=False), is_profile=True),
                Expr(src=ConstantTimeVector(4.0, is_zero_one_profile=False), is_profile=True),
            ],
        ),
    ],
)
def test_verify_operations_there_can_be_no_other_operations_after_division(operations: str, expressions: list[Expr]):
    expr = Expr(
        is_profile=True,
        operations=(
            operations,
            expressions,
        ),
    )

    with pytest.raises(ValueError, match=r"^Found \+-\* after \/ in operations"):
        expr._verify_operations(expect_ops=True)


def test_is_leaf_when_not_operation_expression():
    expr = Expr(src="time_vector1", is_profile=True)

    assert expr.is_leaf() is True


def test_is_not_leaf_when_operation_expression():
    expr = Expr(
        is_profile=True,
        operations=(
            r"*",
            [
                Expr(src="time_vector1", is_profile=True),
                Expr(src="time_vector2", is_profile=True),
            ],
        ),
    )

    assert expr.is_leaf() is False


@pytest.mark.parametrize(
    ("expr1", "expr2", "expected_equal"),
    [
        # Identical exprs
        (
            Expr(
                src="time_vector1",
                is_stock=False,
                is_profile=True,
                operations=("", []),
            ),
            Expr(
                src="time_vector1",
                is_stock=False,
                is_profile=True,
                operations=("", []),
            ),
            True,
        ),
        # Different src
        (
            Expr(
                src="time_vector1",
                is_stock=False,
                is_profile=True,
                operations=("", []),
            ),
            Expr(
                src=ConstantTimeVector(scalar=1.0, is_zero_one_profile=False),
                is_stock=False,
                is_profile=True,
                operations=("", []),
            ),
            False,
        ),
        # Different operations
        (
            Expr(
                src="time_vector1",
                is_stock=False,
                is_profile=True,
                operations=("", []),
            ),
            Expr(
                src="time_vector1",
                is_stock=False,
                is_profile=True,
                operations=("*", [Expr(src="time_vector1", is_stock=False, is_profile=True), Expr(src="time_vector2", is_stock=False, is_profile=True)]),
            ),
            False,
        ),
        # Different profile
        (
            Expr(
                src="time_vector1",
                is_stock=False,
                is_profile=True,
                profile=None,
                operations=("", []),
            ),
            Expr(
                src="time_vector1",
                is_stock=False,
                is_profile=True,
                profile=Expr(src="profile_vector", is_profile=True),
                operations=("", []),
            ),
            False,
        ),
        # Identical operation exprs with identical args
        (
            Expr(
                is_profile=True,
                operations=(
                    "*",
                    [
                        Expr(src="time_vector1", is_stock=False, is_profile=True),
                        Expr(src="time_vector2", is_stock=False, is_profile=True),
                    ],
                ),
            ),
            Expr(
                is_profile=True,
                operations=(
                    "*",
                    [
                        Expr(src="time_vector1", is_stock=False, is_profile=True),
                        Expr(src="time_vector2", is_stock=False, is_profile=True),
                    ],
                ),
            ),
            True,
        ),
    ],
)
def test_expr_hash_and_equality(expr1, expr2, expected_equal):
    if expected_equal:
        assert hash(expr1) == hash(expr2)
        assert expr1 == expr2
    else:
        assert hash(expr1) != hash(expr2)
        assert expr1 != expr2


def _mock_timevector_loader() -> TimeVectorLoader:
    loader = Mock(TimeVectorLoader)
    loader.get_unit.return_value = "MW"
    loader.is_max_level.return_value = True
    loader.is_zero_one_profile.return_value = None
    return loader


def _mock_curve_loader() -> CurveLoader:
    return Mock(CurveLoader)


def test_add_loaders_with_timevector_loader_added():
    loader = _mock_timevector_loader()
    expr = Expr(src=LoadedTimeVector("vector_1", loader=loader))
    loaders = set()

    expr.add_loaders(loaders)

    assert loader in loaders


def test_add_loaders_with_curve_loader_added():
    loader = _mock_curve_loader()
    expr = Expr(src=LoadedCurve("curve_1", loader=loader))
    loaders = set()

    expr.add_loaders(loaders)

    assert loader in loaders


def test_add_loaders_with_no_loader_in_timevector():
    expr = Expr(src=ConstantTimeVector(scalar=1.0, is_zero_one_profile=False))
    loaders = set()

    expr.add_loaders(loaders)

    assert loaders == set()


def test_add_loaders_with_no_loader_in_curve():
    curve = Mock(Curve)
    expr = Expr(src=curve)
    loaders = set()

    expr.add_loaders(loaders)

    assert loaders == set()


def test_add_loaders_with_operation_expression_recurses(monkeypatch):
    loader1 = _mock_timevector_loader()
    loader2 = _mock_timevector_loader()
    expr1 = Expr(src=LoadedTimeVector("vector_1", loader=loader1))
    expr2 = Expr(src=LoadedTimeVector("vector_2", loader=loader2))
    op_expr = Expr(operations=("+", [expr1, expr2]))
    loaders = set()

    op_expr.add_loaders(loaders)

    assert loader1 in loaders
    assert loader2 in loaders


def test_add_loaders_with_mixed_none_and_loader(monkeypatch):
    loader = _mock_timevector_loader()
    expr1 = Expr(src=LoadedTimeVector("vector_1", loader=loader))
    expr2 = Expr(src=ConstantTimeVector(scalar=1.0, is_zero_one_profile=False))
    op_expr = Expr(operations=("+", [expr1, expr2]))
    loaders = set()

    op_expr.add_loaders(loaders)

    assert loader in loaders
    assert len(loaders) == 1


def test_add_loaders_with_nested_operations():
    loader1 = _mock_timevector_loader()
    loader2 = _mock_timevector_loader()
    loader3 = _mock_timevector_loader()
    expr1 = Expr(src=LoadedTimeVector("vector_1", loader=loader1))
    expr2 = Expr(src=LoadedTimeVector("vector_2", loader=loader2))
    add_expr = expr1 + expr2
    expr3 = Expr(src=LoadedTimeVector("vector_3", loader=loader3))
    expr = add_expr * expr3
    loaders = set()

    expr.add_loaders(loaders)

    assert len(loaders) == 3
    assert loader1 in loaders
    assert loader2 in loaders
    assert loader3 in loaders


def _expr() -> Expr:
    return Expr(src=ConstantTimeVector(1.0, is_zero_one_profile=False), is_profile=True)


def test_check_operations_allows_none_operations():
    expr = _expr()
    expr._check_operations(None)


def test_check_operations_non_tuple_should_raise():
    expr = _expr()
    with pytest.raises(TypeError):
        expr._check_operations(["+", [_expr(), _expr()]])


def test_check_operations_wrong_length_should_raise():
    expr = _expr()
    with pytest.raises(ValueError, match="Expected len\\(operations\\) == 2. Got:"):
        expr._check_operations(("+", [_expr()] * 3, "extra"))


def test_check_operations_ops_not_str_should_raise():
    expr = _expr()
    with pytest.raises(TypeError):
        expr._check_operations((1, [_expr(), _expr()]))


def test_check_operations_args_not_list_should_raise():
    expr = _expr()
    with pytest.raises(TypeError):
        expr._check_operations(("+", "not_a_list"))


def test_check_operations_empty_ops_with_args_should_raise():
    expr = _expr()
    with pytest.raises(ValueError, match="Expected ops to have length. Got"):
        expr._check_operations(("", [_expr()]))


def test_check_operations_empty_ops_with_expect_ops_should_raise():
    expr = _expr()
    with pytest.raises(ValueError, match="Expected ops, but got"):
        expr._check_operations(("", []), expect_ops=True)


def test_check_operations_ops_args_length_mismatch_should_raise():
    expr = _expr()
    with pytest.raises(ValueError, match="Expected len\\(ops\\) == len\\(args\\) - 1. Got"):
        expr._check_operations(("+*", [_expr(), _expr()]))


def test_check_operations_invalid_op_should_raise():
    expr = _expr()
    with pytest.raises(ValueError, match="Expected all op in ops in \\+-\\*/. Got"):
        expr._check_operations(("%", [_expr(), _expr()]))


def test_check_operations_args_not_expr_should_raise():
    expr = _expr()
    with pytest.raises(TypeError):
        expr._check_operations(("+", [_expr(), 123]))


def test_check_operations_valid_ops_should_not_raise():
    expr = _expr()
    expr._check_operations(("+", [_expr(), _expr()]))


def test_check_operations_valid_multiple_ops_should_not_raise():
    expr = _expr()
    expr._check_operations(("+*", [_expr(), _expr(), _expr()]))
