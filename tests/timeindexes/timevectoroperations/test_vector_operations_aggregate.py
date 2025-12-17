import numpy as np
import pytest

from framcore.timeindexes._time_vector_operations import aggregate


def test_when_aggrfunc_sum_should_sum_values():
    in_x = np.ones(52 * 168, dtype=np.float32)
    out_x = np.zeros(52, dtype=np.float32)

    aggregate(in_x, out_x, is_aggfunc_sum=True)

    assert np.size(out_x) == 52
    assert np.all(out_x == 168)


def test_when_aggrfunc_mean_should_mean_values():
    in_x = np.ones(52 * 168, dtype=np.float32)
    out_x = np.zeros(52, dtype=np.float32)

    aggregate(in_x, out_x, is_aggfunc_sum=False)

    assert np.size(out_x) == 52
    assert np.all(out_x == 1)


def test_when_input_array_is_not_vector_raise_exception():
    in_x = np.ones((52, 168), dtype=np.float32)
    out_x = np.zeros(52, dtype=np.float32)

    with pytest.raises(AssertionError):
        aggregate(in_x, out_x, is_aggfunc_sum=True)


def test_when_output_array_is_not_vector_raise_exception():
    in_x = np.ones(52 * 168, dtype=np.float32)
    out_x = np.zeros((52, 1), dtype=np.float32)

    with pytest.raises(AssertionError):
        aggregate(in_x, out_x, is_aggfunc_sum=True)


def test_when_input_array_size_is_greater_than_output_array_size_raise_exception():
    in_x = np.ones(52 * 168, dtype=np.float32)
    out_x = np.zeros(53, dtype=np.float32)

    with pytest.raises(AssertionError):
        aggregate(in_x, out_x, is_aggfunc_sum=True)


def test_when_input_vector_size_is_not_multiplier_of_output_vector_size_raise_exception():
    in_x = np.ones(52 * 168, dtype=np.float32)
    out_x = np.zeros(51, dtype=np.float32)

    with pytest.raises(AssertionError):
        aggregate(in_x, out_x, is_aggfunc_sum=True)


def test_when_input_vector_is_different_type_then_output_vector_raise_exception():
    in_x = np.ones(52 * 168, dtype=np.float32)
    out_x = np.zeros(52, dtype=np.float64)

    with pytest.raises(AssertionError):
        aggregate(in_x, out_x, is_aggfunc_sum=True)
