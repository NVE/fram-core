from unittest.mock import Mock

import pytest

from framcore.expressions import Expr
from framcore.metadata import Div, ExprMeta, Meta
from framcore.timevectors import ConstantTimeVector


def test_init():
    expr = Mock(Expr)

    expr_meta = ExprMeta(value=expr)

    assert expr_meta.get_value() == expr


@pytest.mark.parametrize(
    "invalid_value",
    [
        42,
        "invalid_string",
        3.14,
        [Mock(Expr)],
        None,
    ],
)
def test_init_invalid_type_raises(invalid_value):
    with pytest.raises(TypeError):
        ExprMeta(value=invalid_value)


def test_eq_same_value():
    expr = Mock(Expr)

    expr_meta1 = ExprMeta(value=expr)
    expr_meta2 = ExprMeta(value=expr)

    assert expr_meta1 == expr_meta2


def test_eq_different_value():
    expr1 = Mock(Expr)
    expr2 = Mock(Expr)

    expr_meta1 = ExprMeta(value=expr1)
    expr_meta2 = ExprMeta(value=expr2)

    assert expr_meta1 != expr_meta2


def test_eq_different_type():
    expr = Mock(Expr)

    expr_meta = ExprMeta(value=expr)
    other_meta = Div()

    assert expr_meta != other_meta


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        (Expr(src=ConstantTimeVector(scalar=1.0, is_max_level=True)), True),
        (Expr(src=ConstantTimeVector(scalar=1.0, is_max_level=False)), False),
    ],
)
def test_hash(expr, expected):
    expr_meta1 = ExprMeta(value=Expr(src=ConstantTimeVector(scalar=1.0, is_max_level=True)))
    expr_meta2 = ExprMeta(value=expr)

    assert (hash(expr_meta1) == hash(expr_meta2)) is expected


def test_combine_with_exprmeta():
    expr1 = Expr(src=ConstantTimeVector(scalar=1.0, is_max_level=True))
    expr2 = Expr(src=ConstantTimeVector(scalar=2.0, is_max_level=True))

    expr_meta1 = ExprMeta(value=expr1)
    expr_meta2 = ExprMeta(value=expr2)

    combined = expr_meta1.combine(expr_meta2)

    assert isinstance(combined, Expr)
    assert combined.get_src() == ConstantTimeVector(scalar=3.0, is_max_level=True)


def test_combine_with_div():
    expr = Expr("time_vector")
    expr_meta = ExprMeta(value=expr)
    div = Div()

    combined = expr_meta.combine(div)

    assert isinstance(combined, Div)
    assert expr_meta in combined.get_value()
    assert div in combined.get_value()

def test_combine_with_other_meta():
    expr = Expr("time_vector")
    expr_meta = ExprMeta(value=expr)
    other_meta = Mock(Meta)

    combined = expr_meta.combine(other_meta)

    assert isinstance(combined, Div)
    assert expr_meta in combined.get_value()
    assert other_meta in combined.get_value()

def test_equal_exprmeta_should_have_same_fingerprint():
    expr = Expr(src=ConstantTimeVector(scalar=1.0, is_max_level=True))

    expr_meta1 = ExprMeta(value=expr)
    expr_meta2 = ExprMeta(value=expr)

    assert expr_meta1.get_fingerprint() == expr_meta2.get_fingerprint()

def test_different_exprmeta_should_have_different_fingerprint():
    expr1 = Expr(src=ConstantTimeVector(scalar=1.0, is_max_level=True))
    expr2 = Expr(src=ConstantTimeVector(scalar=2.0, is_max_level=True))

    expr_meta1 = ExprMeta(value=expr1)
    expr_meta2 = ExprMeta(value=expr2)

    assert expr_meta1.get_fingerprint() != expr_meta2.get_fingerprint()
