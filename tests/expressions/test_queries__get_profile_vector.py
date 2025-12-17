from datetime import timedelta
from unittest.mock import Mock

import pytest

from framcore import Model
from framcore.expressions import Expr, get_profile_vector
from framcore.querydbs import ModelDB, QueryDB
from framcore.timeindexes import FixedFrequencyTimeIndex, ModelYear, ProfileTimeIndex, SinglePeriodTimeIndex, TimeIndex
from framcore.timevectors import ConstantTimeVector


@pytest.mark.parametrize(
    ("expr", "db", "data_dim", "scen_dim", "is_zero_one", "is_float32"),
    [
        ("not_an_expr", Mock(QueryDB), Mock(SinglePeriodTimeIndex), Mock(FixedFrequencyTimeIndex), False, False),
        # (Mock(Expr), "not_query_db", Mock(SinglePeriodTimeIndex), Mock(FixedFrequencyTimeIndex), False, False),
        (Mock(Expr), Mock(QueryDB), Mock(TimeIndex), Mock(FixedFrequencyTimeIndex), False, False),
        (Mock(Expr), Mock(QueryDB), Mock(SinglePeriodTimeIndex), Mock(TimeIndex), False, False),
        (Mock(Expr), Mock(QueryDB), Mock(TimeIndex), Mock(FixedFrequencyTimeIndex), "not_a_bool", False),
        (Mock(Expr), Mock(QueryDB), Mock(SinglePeriodTimeIndex), Mock(TimeIndex), False, "not_a_bool"),
    ],
)
def test_get_profile_vector_with_invalid_params_raises_type_error(expr, db, data_dim, scen_dim, is_zero_one, is_float32):
    with pytest.raises(TypeError):
        get_profile_vector(expr=expr, db=db, data_dim=data_dim, scen_dim=scen_dim, is_zero_one=is_zero_one, is_float32=is_float32)


def _profile_timevector(scalar: float, unit: str = "MW") -> ConstantTimeVector:
    return ConstantTimeVector(scalar, unit=unit, is_zero_one_profile=True, reference_period=None)


def _model_year() -> ModelYear:
    return ModelYear(2025)


def _profile_time_index() -> ProfileTimeIndex:
    return ProfileTimeIndex(1981, 10, timedelta(days=1), is_52_week_years=True)


def test_get_profile_vector_leaf_expr():
    model = Model()
    data = model.get_data()

    profile_tv = _profile_timevector(scalar=0.5, unit=None)
    data["profile_tv"] = profile_tv

    profile_expr = Expr(src="profile_tv", is_profile=True)

    query_db = ModelDB(model)

    profile_vector = get_profile_vector(
        profile_expr,
        query_db,
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_zero_one=True,
    )

    assert all(value == 0.5 for value in profile_vector), "All values in the profile vector should be 0.5"

def test_get_profile_vector_leaf_expr_with_timevector_as_src():
    model = Model()

    profile_tv = _profile_timevector(scalar=0.4, unit=None)
    # data["profile_tv"] = profile_tv

    src_expr = Expr(src=profile_tv, is_profile=True)

    query_db = ModelDB(model)

    profile_vector = get_profile_vector(
        src_expr,
        query_db,
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_zero_one=True,
    )

    assert all(value == 0.4 for value in profile_vector), "All values in the profile vector should be 0.4"


def test_get_profile_vector_sum_expr():
    model = Model()
    data = model.get_data()

    profile_tv_1 = _profile_timevector(scalar=0.3, unit=None)
    profile_tv_2 = _profile_timevector(scalar=0.7, unit=None)
    profile_tv_3 = _profile_timevector(scalar=0.5, unit=None)
    data["profile_tv_1"] = profile_tv_1
    data["profile_tv_2"] = profile_tv_2
    data["profile_tv_3"] = profile_tv_3

    expr_1 = Expr(src="profile_tv_1", is_profile=True)
    expr_2 = Expr(src="profile_tv_2", is_profile=True)
    expr_3 = Expr(src="profile_tv_3", is_profile=True)

    sum_expr = expr_1 + expr_2 + expr_3

    query_db = ModelDB(model)

    profile_vector = get_profile_vector(
        sum_expr,
        query_db,
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_zero_one=True,
    )

    assert all(value == 1.5 for value in profile_vector), "All values in the profile vector should be 1.5"


def test_get_profile_vector_multiplication_expr():
    model = Model()
    data = model.get_data()

    profile_tv = _profile_timevector(scalar=0.25, unit=None)
    data["profile_tv"] = profile_tv

    expr1 = Expr(src="profile_tv", is_profile=True)

    mul_expr = 2 * expr1

    query_db = ModelDB(model)

    profile_vector = get_profile_vector(
        mul_expr,
        query_db,
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_zero_one=True,
    )

    assert all(value == 0.5 for value in profile_vector), "All values in the profile vector should be 0.5"


def test_get_profile_vector_illegal_expr_raises_value_error():
    model = Model()
    data = model.get_data()

    profile_tv_1 = _profile_timevector(scalar=0.3, unit=None)
    profile_tv_2 = _profile_timevector(scalar=0.7, unit=None)
    data["profile_tv_1"] = profile_tv_1
    data["profile_tv_2"] = profile_tv_2

    expr_1 = Expr(src="profile_tv_1", is_profile=True)
    expr_2 = Expr(src="profile_tv_2", is_profile=True)

    sum_expr = (expr_2 - expr_1) * 2

    query_db = ModelDB(model)

    with pytest.raises(ValueError, match="Expected"):
        get_profile_vector(
            sum_expr,
            query_db,
            data_dim=_model_year(),
            scen_dim=_profile_time_index(),
            is_zero_one=True,
        )


def test_get_profile_vector_nested_expr():
    model = Model()
    data = model.get_data()

    profile_tv = _profile_timevector(scalar=0.6, unit=None)
    data["profile_tv"] = profile_tv

    inner_expr = Expr(src="profile_tv", is_profile=True)
    data["inner_expr"] = inner_expr

    outer_expr = Expr(src="inner_expr", is_profile=True)

    query_db = ModelDB(model)

    profile_vector = get_profile_vector(
        outer_expr,
        query_db,
        data_dim=_model_year(),
        scen_dim=_profile_time_index(),
        is_zero_one=True,
    )

    assert all(value == 0.6 for value in profile_vector), "All values in the profile vector should be 0.6"


def test_get_profile_vector_expr_with_non_profile_leaf_raises_value_error():
    model = Model()
    data = model.get_data()

    profile_tv = _profile_timevector(scalar=0.4, unit=None)
    none_profile_expr = Expr(src=profile_tv, is_profile=False)
    data["none_profile_expr"] = none_profile_expr

    src_expr = Expr(src="none_profile_expr", is_profile=True)

    query_db = ModelDB(model)

    match_regex = r"Expected .+? to be is_profile=True\."
    with pytest.raises(ValueError, match=match_regex):
        get_profile_vector(
            src_expr,
            query_db,
            data_dim=_model_year(),
            scen_dim=_profile_time_index(),
            is_zero_one=True,
        )
