import pytest

from framcore.timevectors import ReferencePeriod


def test_init_start_year_must_be_positive_int():
    with pytest.raises(ValueError, match="start_year must be a positive integer. Got -2020."):
        ReferencePeriod(start_year=-2020, num_years=1)

def test_init_num_years_must_be_positive_non_zero_int():
    with pytest.raises(ValueError, match="num_years must be a positive non-zero integer. Got 0."):
        ReferencePeriod(start_year=2020, num_years=0)

    with pytest.raises(ValueError, match="num_years must be a positive non-zero integer. Got -1."):
        ReferencePeriod(start_year=2020, num_years=-1)

def test_init_valid_reference_period():
    ref_period = ReferencePeriod(start_year=2020, num_years=3)
    assert ref_period.get_start_year() == 2020
    assert ref_period.get_num_years() == 3

@pytest.mark.parametrize(("ref_period", "expected_equal"), [
    (ReferencePeriod(start_year=2021, num_years=1), True),
    (ReferencePeriod(start_year=2022, num_years=1), False),
    (ReferencePeriod(start_year=2021, num_years=2), False),
])
def test_eq_(ref_period: ReferencePeriod, expected_equal: bool):
    ref_period1 = ReferencePeriod(start_year=2021, num_years=1)

    assert (ref_period1 == ref_period) is expected_equal

@pytest.mark.parametrize(("ref_period", "expected_equal"), [
    (ReferencePeriod(start_year=2021, num_years=1), True),
    (ReferencePeriod(start_year=2022, num_years=1), False),
    (ReferencePeriod(start_year=2021, num_years=2), False),
])
def test_hash_(ref_period: ReferencePeriod, expected_equal: bool):
    ref_period1 = ReferencePeriod(start_year=2021, num_years=1)

    assert (hash(ref_period1) == hash(ref_period)) is expected_equal
