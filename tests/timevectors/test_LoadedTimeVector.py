from unittest.mock import MagicMock, Mock

import numpy as np
import pytest
from numpy.typing import NDArray

from framcore.loaders import TimeVectorLoader
from framcore.timevectors import LoadedTimeVector, ReferencePeriod


def _mock_loader(is_max_level: bool | None, is_zero_one_profile: bool | None) -> TimeVectorLoader:
    loader = Mock(TimeVectorLoader)
    loader.is_max_level.return_value = is_max_level
    loader.is_zero_one_profile.return_value = is_zero_one_profile
    loader.get_unit.return_value = "MW"
    loader.get_reference_period.return_value = ReferencePeriod(start_year=2020, num_years=1)
    loader.get_values.return_value = np.array([2.0, 3.0, 4.0], dtype=np.float32)
    return loader


@pytest.mark.parametrize(
    "loader",
    [
        _mock_loader(None, None),
        _mock_loader(True, True),
        _mock_loader(False, False),
        _mock_loader(True, False),
        _mock_loader(False, True),
    ],
)
def test_init_must_be_either_level_or_profile(loader: TimeVectorLoader):
    with pytest.raises(ValueError, match="Invalid input arguments for LoadedTimeVector"):
        LoadedTimeVector(
            vector_id="vector_1",
            loader=loader,
        )


def test_init_level():
    loader = _mock_loader(True, None)
    vector = LoadedTimeVector(
        vector_id="vector_1",
        loader=loader,
    )

    assert vector.is_max_level() is True
    assert vector.is_zero_one_profile() is None
    assert vector.get_loader() == loader
    assert vector.get_unit() == "MW"
    assert vector.get_reference_period() == ReferencePeriod(start_year=2020, num_years=1)


def test_init_profile():
    loader = _mock_loader(None, True)
    vector = LoadedTimeVector(
        vector_id="vector_1",
        loader=loader,
    )

    assert vector.is_max_level() is None
    assert vector.is_zero_one_profile() is True
    assert vector.get_loader() == loader
    assert vector.get_unit() == "MW"
    assert vector.get_reference_period() == ReferencePeriod(start_year=2020, num_years=1)


@pytest.mark.parametrize(
    ("vector_id", "loader", "expected_equal"),
    [
        ("vector_1", None, True),  # Same vector_id and reuse loader
        ("vector_2", None, False),  # Different vector_id and reuse loader
        ("vector_1", _mock_loader(True, None), False),  # Same vector_id but different loader
    ],
)
def test_eq_(vector_id: str, loader: TimeVectorLoader | None, expected_equal: bool):
    _loader = _mock_loader(None, True)

    vector1 = LoadedTimeVector(
        vector_id="vector_1",
        loader=_loader,
    )

    vector2 = LoadedTimeVector(
        vector_id=vector_id,
        loader=loader if loader is not None else _loader,
    )

    assert (vector1 == vector2) is expected_equal


@pytest.mark.parametrize(
    ("vector_id", "loader", "expected_equal"),
    [
        ("vector_1", None, True),  # Same vector_id and reuse loader
        ("vector_2", None, False),  # Different vector_id and reuse loader
        ("vector_1", _mock_loader(True, None), False),  # Same vector_id but different loader
    ],
)
def test_hash_(vector_id: str, loader: TimeVectorLoader | None, expected_equal: bool):
    _loader = _mock_loader(None, True)

    vector1 = LoadedTimeVector(
        vector_id="vector_1",
        loader=_loader,
    )

    vector2 = LoadedTimeVector(
        vector_id=vector_id,
        loader=loader if loader is not None else _loader,
    )

    assert (hash(vector1) == hash(vector2)) is expected_equal


@pytest.mark.parametrize(
    ("dtype", "expected_vector"),
    [
        (np.float32, np.array([2.0, 3.0, 4.0], dtype=np.float32)),
        (np.float64, np.array([2.0, 3.0, 4.0], dtype=np.float64)),
    ],
)
def test_get_vector(dtype: np.dtype, expected_vector: NDArray):
    vector = LoadedTimeVector(
        vector_id="vector_1",
        loader=_mock_loader(None, True),
    )

    is_float32 = dtype == np.float32
    result = vector.get_vector(is_float32=is_float32)

    assert np.array_equal(result, expected_vector)


def test_get_time_index():
    class TestLoadedTimeVector(LoadedTimeVector):
        def __init__(self, vector_id, loader) -> None:
            self._vector_id = vector_id
            self._loader = loader

    expected = "index"
    mocked_loader = MagicMock()
    mocked_loader_get_index = Mock(return_value=expected)
    mocked_loader.get_index = mocked_loader_get_index

    test_id = "test_id"
    test_tv = TestLoadedTimeVector(test_id, mocked_loader)

    result = test_tv.get_timeindex()
    assert result == expected
    mocked_loader_get_index.assert_called_once()


def test_is_constant():
    vector = LoadedTimeVector(
        vector_id="vector_1",
        loader=_mock_loader(None, True),
    )

    assert vector.is_constant() is False
