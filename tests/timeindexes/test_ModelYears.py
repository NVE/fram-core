from datetime import datetime

import pytest

from framcore.timeindexes import ModelYears


def test_model_years_single_year():
    years = [2021]

    index = ModelYears(years)

    assert index.is_52_week_years() is False
    assert index.extrapolate_first_point() is True
    assert index.extrapolate_last_point() is True
    assert index.get_num_periods() == 1
    assert len(index.get_datetime_list()) == 2
    assert index.get_datetime_list() == [datetime(2021, 1, 4), datetime(2022, 1, 3)]


def test_model_years_multiple_years():
    years = [2019, 2020, 2021]

    index = ModelYears(years)

    assert index.is_52_week_years() is False
    assert index.extrapolate_first_point() is True
    assert index.extrapolate_last_point() is True
    assert index.get_num_periods() == 3
    assert len(index.get_datetime_list()) == 4
    assert index.get_datetime_list() == [
        datetime(2018, 12, 31),
        datetime(2019, 12, 30),
        datetime(2021, 1, 4),
        datetime(2022, 1, 3),
    ]


@pytest.mark.parametrize(
    "years",
    [
        [],
        None,
    ],
)
def test_expect_at_least_one_year(years: list[int] | None):
    with pytest.raises(ValueError, match="At least one year must be provided."):
        ModelYears(years)


def test_expect_ordered_years():
    years = [2020, 2021, 2019]

    with pytest.raises(ValueError, match="All elements of datetime_list must be smaller"):
        ModelYears(years)
