from unittest.mock import Mock

import pytest

from framcore.expressions import Expr
from framcore.metadata import LevelExprMeta
from framcore.timevectors import ConstantTimeVector, TimeVector


@pytest.mark.parametrize(
    "value",
    [
        Expr(src=ConstantTimeVector(scalar=1.0, is_max_level=True), is_level=True),
        ConstantTimeVector(scalar=1.0, is_max_level=True),
    ],
)
def test_init_valid_inputs(value: Expr | TimeVector):
    meta = LevelExprMeta(value=value)

    assert isinstance(meta.get_value(), Expr)


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
def test_init_invalid_input_type_raises(invalid_value):
    with pytest.raises(TypeError):
        LevelExprMeta(value=invalid_value)


@pytest.mark.parametrize(
    "value",
    [
        Expr(src=ConstantTimeVector(scalar=1.0, is_zero_one_profile=True), is_profile=True),
        ConstantTimeVector(scalar=1.0, is_zero_one_profile=True),
    ],
)
def test_init_non_level_input_raises(value):
    with pytest.raises(ValueError, match=".+"):
        LevelExprMeta(value=value)
