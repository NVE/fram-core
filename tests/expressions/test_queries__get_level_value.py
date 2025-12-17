import operator
from datetime import timedelta
from unittest.mock import Mock

import pytest

from framcore import Model
from framcore.expressions import Expr, get_level_value
from framcore.querydbs import ModelDB, QueryDB
from framcore.timeindexes import FixedFrequencyTimeIndex, ModelYear, ProfileTimeIndex, SinglePeriodTimeIndex, TimeIndex
from framcore.timevectors import ConstantTimeVector


@pytest.mark.parametrize(
    ("expr", "db", "unit", "data_dim", "scen_dim", "is_max"),
    [
        ("not_an_expr", Mock(QueryDB), "kW", Mock(SinglePeriodTimeIndex), Mock(FixedFrequencyTimeIndex), False),
        # (Mock(Expr), "not_query_db", "MW", Mock(SinglePeriodTimeIndex), Mock(FixedFrequencyTimeIndex), True),
        (Mock(Expr), Mock(QueryDB), 100.0, Mock(SinglePeriodTimeIndex), Mock(FixedFrequencyTimeIndex), True),
        (Mock(Expr), Mock(QueryDB), "MW", Mock(TimeIndex), Mock(FixedFrequencyTimeIndex), True),
        (Mock(Expr), Mock(QueryDB), "MW", Mock(SinglePeriodTimeIndex), Mock(TimeIndex), True),
        (Mock(Expr), Mock(QueryDB), "MW", Mock(SinglePeriodTimeIndex), Mock(FixedFrequencyTimeIndex), "not_a_bool"),
    ],
)
def test_get_level_value_with_invalid_params_raises_type_error(expr, db, unit, data_dim, scen_dim, is_max):
    with pytest.raises(TypeError):
        get_level_value(expr=expr, db=db, unit=unit, data_dim=data_dim, scen_dim=scen_dim, is_max=is_max)


def _level_timevector(scalar: float = 0.0, unit: str = "MW") -> ConstantTimeVector:
    return ConstantTimeVector(scalar, unit=unit, is_max_level=True, reference_period=None)


def _model_year() -> ModelYear:
    return ModelYear(2025)


def _profile_time_index() -> ProfileTimeIndex:
    return ProfileTimeIndex(1981, 10, timedelta(days=1), is_52_week_years=True)


def test_get_level_value_with_leaf_expr():
    model = Model()
    data = model.get_data()

    level_tv = _level_timevector(scalar=200.0)
    data["level_tv"] = level_tv

    level_expr = Expr(src="level_tv", is_level=True)

    db = ModelDB(model)

    level_value = get_level_value(
        level_expr,
        db=db,
        unit="MW",
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_max=True,
    )

    assert level_value == 200.0, f"Expected 200.0, got {level_value}"


@pytest.mark.parametrize(
    ("operation", "expected_value"),
    [
        (operator.add, 25.0),
        (operator.sub, 5.0),
        (operator.mul, 150.0),
    ],
    ids=["add", "sub", "mul"],
)
def test_get_level_value_single_ops(operation: callable, expected_value: float):
    model = Model()
    data = model.get_data()

    level_tv1 = _level_timevector(scalar=15.0)
    data["level_tv1"] = level_tv1

    level_tv2 = _level_timevector(scalar=10.0)
    data["level_tv2"] = level_tv2

    level_expr1 = Expr(src="level_tv1", is_level=True)
    level_expr2 = Expr(src="level_tv2", is_level=True)

    operation_expr = operation(level_expr1, level_expr2)

    query_db = ModelDB(model)

    level_value = get_level_value(
        operation_expr,
        db=query_db,
        unit="MW",
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_max=True,
    )

    assert level_value == expected_value, f"Expected {expected_value}, got {level_value}"


def test_get_level_value_with_multiple_operations_and_division():
    model = Model()
    data = model.get_data()

    level_tv1 = _level_timevector(scalar=150.0)
    data["level_tv1"] = level_tv1

    level_tv2 = _level_timevector(scalar=20.0)
    data["level_tv2"] = level_tv2

    level_tv3 = _level_timevector(scalar=5.0, unit=None)
    data["level_tv3"] = level_tv3

    level_tv4 = _level_timevector(scalar=2.0, unit=None)
    data["level_tv4"] = level_tv4

    level_expr1 = Expr(src="level_tv1", is_level=True)
    level_expr2 = Expr(src="level_tv2", is_level=True)
    level_expr3 = Expr(src="level_tv3", is_level=True)
    level_expr4 = Expr(src="level_tv4", is_level=True)

    nested_expr = (level_expr1 - (level_expr2 * level_expr3)) / level_expr4

    query_db = ModelDB(model)

    level_value = get_level_value(
        nested_expr,
        db=query_db,
        unit="MW",
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_max=True,
    )

    expected_value = (150.0 - (20.0 * 5.0)) / 2.0  # (150 - 100) / 2 = 25.0
    assert level_value == expected_value, f"Expected {expected_value}, got {level_value}"


def test_get_level_value_complex_expr_no_fastpath():
    model = Model()
    data = model.get_data()

    level_tv1 = _level_timevector(scalar=50.0)
    data["level_tv1"] = level_tv1

    level_tv2 = _level_timevector(scalar=30.0)
    data["level_tv2"] = level_tv2

    level_tv3 = _level_timevector(scalar=10.0, unit=None)
    data["level_tv3"] = level_tv3

    level_expr1 = Expr(src="level_tv1", is_level=True)
    level_expr2 = Expr(src="level_tv2", is_level=True)
    level_expr3 = Expr(src="level_tv3", is_level=True)

    complex_expr = (level_expr1 + level_expr2) * level_expr3 - (level_expr2 / level_expr3)

    query_db = ModelDB(model)

    level_value = get_level_value(
        complex_expr,
        db=query_db,
        unit="MW",
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_max=True,
    )

    expected_value = (50.0 + 30.0) * 10.0 - 30.0 / 10.0  # (80 * 10) - 3 = 797.0
    assert level_value == expected_value, f"Expected {expected_value}, got {level_value}"
