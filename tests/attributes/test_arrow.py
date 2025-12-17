from unittest.mock import Mock

import numpy as np
import pytest

from framcore.attributes import Conversion, Efficiency, Loss
from framcore.attributes.Arrow import Arrow
from framcore.querydbs import QueryDB
from framcore.timeindexes import FixedFrequencyTimeIndex, SinglePeriodTimeIndex
from framcore.timeindexes.ModelYear import ModelYear


def mock_conversion(has_profile: bool = False, scenario_vector: np.ndarray = None, data_value: float | None = None):
    """Mock Conversion object."""
    conversion = Mock(spec=Conversion)
    conversion.has_profile.return_value = has_profile
    conversion.has_level.return_value = not has_profile
    conversion.get_data_value.return_value = data_value
    conversion.get_level_unit_set.return_value = {"MWh"}
    conversion.get_profile_timeindex_set.return_value = {ModelYear(2020)}
    conversion.get_scenario_vector.return_value = scenario_vector
    return conversion


def mock_efficiency(has_profile: bool = False, scenario_vector: np.ndarray = None, data_value: float | None = None):
    """Mock Efficiency object."""
    efficiency = Mock(spec=Efficiency)
    efficiency.has_profile.return_value = has_profile
    efficiency.has_level.return_value = not has_profile
    efficiency.get_data_value.return_value = data_value
    efficiency.get_profile_timeindex_set.return_value = {ModelYear(2021)}
    efficiency.get_scenario_vector.return_value = scenario_vector
    return efficiency


def mock_loss(has_profile: bool = False, scenario_vector: np.ndarray = None, data_value: float | None = None):
    """Mock Loss object."""
    loss = Mock(spec=Loss)
    loss.has_profile.return_value = has_profile
    loss.has_level.return_value = not has_profile
    loss.get_data_value.return_value = data_value
    loss.get_profile_timeindex_set.return_value = {ModelYear(2022)}
    loss.get_scenario_vector.return_value = scenario_vector
    return loss


def mock_db():
    """Mock QueryDB object."""
    return Mock(spec=QueryDB)


def mock_scenario_horizon():
    """Mock FixedFrequencyTimeIndex."""
    horizon = Mock(spec=FixedFrequencyTimeIndex)
    horizon.get_num_periods.return_value = 7
    return horizon


def mock_level_period():
    """Mock SinglePeriodTimeIndex."""
    return Mock(spec=SinglePeriodTimeIndex)


def test_has_profile_when_none_of_relevant_attributes_have_profile():
    arrow = Arrow(node="test", is_ingoing=True)
    assert arrow.has_profile() is False


@pytest.mark.parametrize(
    "arrow",
    [
        Arrow(node="test", is_ingoing=True, conversion=mock_conversion(has_profile=True)),
        Arrow(node="test", is_ingoing=True, efficiency=mock_efficiency(has_profile=True)),
        Arrow(node="test", is_ingoing=True, loss=mock_loss(has_profile=True)),
        Arrow(
            node="test",
            is_ingoing=True,
            conversion=mock_conversion(has_profile=True),
            efficiency=mock_efficiency(has_profile=True),
            loss=mock_loss(has_profile=True),
        ),
    ],
)
def test_has_profile_when_conversion_efficiency_or_loss_has_profile(arrow: Arrow):
    assert arrow.has_profile() is True


def test_get_conversion_unit_set_when_conversion_is_none():
    arrow = Arrow(node="test", is_ingoing=True)
    result = arrow.get_conversion_unit_set(mock_db())
    assert result == set()


@pytest.mark.parametrize(
    ("arrow", "expected_result"),
    [
        (Arrow(node="test", is_ingoing=True, conversion=mock_conversion()), {ModelYear(2020)}),
        (Arrow(node="test", is_ingoing=True, loss=mock_loss()), {ModelYear(2022)}),
        (Arrow(node="test", is_ingoing=True, efficiency=mock_efficiency()), {ModelYear(2021)}),
        (
            Arrow(
                node="test",
                is_ingoing=True,
                conversion=mock_conversion(has_profile=True),
                loss=mock_loss(has_profile=True),
                efficiency=mock_efficiency(has_profile=True),
            ),
            {ModelYear(2020), ModelYear(2021), ModelYear(2022)},
        ),
    ],
)
def test_get_profile_timeindex_set_has_profile(arrow: Arrow, expected_result: set):
    result = arrow.get_profile_timeindex_set(mock_db())

    assert len(result) == len(expected_result)
    assert all(item in result for item in expected_result)


def test_get_scenario_vector_with_only_conversion_and_has_level():
    arrow = Arrow(node="test", is_ingoing=True, conversion=mock_conversion(data_value=2.0))

    result = arrow.get_scenario_vector(mock_db(), mock_scenario_horizon(), mock_level_period(), unit="MWh")

    assert np.equal(result, np.repeat(2.0, 7)).all()


def test_get_scenario_vector_with_only_conversion_and_has_profile():
    arrow = Arrow(node="test", is_ingoing=True, conversion=mock_conversion(has_profile=True, scenario_vector=np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])))

    result = arrow.get_scenario_vector(mock_db(), mock_scenario_horizon(), mock_level_period(), unit="MWh")

    assert np.equal(result, np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])).all()


def test_get_scenario_vector_with_only_efficiency_and_has_level():
    arrow = Arrow(node="test", is_ingoing=True, efficiency=mock_efficiency(data_value=0.8))

    result = arrow.get_scenario_vector(mock_db(), mock_scenario_horizon(), mock_level_period(), unit="MWh")

    assert np.equal(result, np.repeat(1.25, 7)).all()


def test_get_scenario_vector_with_only_efficiency_and_has_profile():
    arrow = Arrow(node="test", is_ingoing=True, efficiency=mock_efficiency(has_profile=True, scenario_vector=np.array([1.0, 2.0, 4.0, 5.0])))

    result = arrow.get_scenario_vector(mock_db(), mock_scenario_horizon(), mock_level_period(), unit="MWh")

    assert np.equal(result, np.array([1.0, 0.5, 0.25, 0.2])).all()


def test_get_scenario_vector_with_only_loss_and_has_level():
    arrow = Arrow(node="test", is_ingoing=True, loss=mock_loss(data_value=0.1))

    result = arrow.get_scenario_vector(mock_db(), mock_scenario_horizon(), mock_level_period(), unit="MWh")

    assert np.equal(result, np.repeat(0.9, 7).astype(np.float32)).all()


def test_get_scenario_vector_with_only_loss_and_has_profile():
    arrow = Arrow(node="test", is_ingoing=True, loss=mock_loss(has_profile=True, scenario_vector=np.array([1.0, 2.0, 4.0, 5.0])))

    result = arrow.get_scenario_vector(mock_db(), mock_scenario_horizon(), mock_level_period(), unit="MWh")

    assert np.equal(result, np.array([0, -1.0, -3.0, -4.0])).all()


@pytest.mark.parametrize(
    ("conversion", "efficiency", "loss", "expected_result"),
    [
        (
            mock_conversion(has_profile=True, scenario_vector=np.array([4.0, 8.0])),
            mock_efficiency(has_profile=True, scenario_vector=np.array([0.8, 0.4])),
            mock_loss(has_profile=True, scenario_vector=np.array([0.1, 0.1])),
            np.array([4.5, 18.0]),
        ),
        (
            mock_conversion(data_value=2.0),
            mock_efficiency(has_profile=True, scenario_vector=np.array([0.8, 0.4])),
            mock_loss(has_profile=True, scenario_vector=np.array([0.1, 0.1])),
            np.array([2.25, 4.5]),
        ),
        (
            mock_conversion(data_value=2.0),
            mock_efficiency(data_value=0.5),
            mock_loss(has_profile=True, scenario_vector=np.array([0.1, 0.2])),
            np.array([3.6, 3.2]),
        ),
        (
            mock_conversion(data_value=2.0),
            mock_efficiency(data_value=0.5),
            mock_loss(data_value=0.1),
            np.array([3.6, 3.6, 3.6, 3.6, 3.6, 3.6, 3.6], dtype=np.float32),
        ),
        (
            mock_conversion(has_profile=True, scenario_vector=np.array([1.0, 2.0])),
            mock_efficiency(data_value=0.5),
            mock_loss(has_profile=True, scenario_vector=np.array([0.1, 0.1])),
            np.array([1.8, 3.6]),
        ),
        (
            mock_conversion(has_profile=True, scenario_vector=np.array([1.0, 2.0])),
            mock_efficiency(has_profile=True, scenario_vector=np.array([0.5, 0.5])),
            mock_loss(data_value=0.1),
            np.array([1.8, 3.6]),
        ),
    ],
)
def test_get_scenario_vector_with_all_attributes(conversion: Conversion, efficiency: Efficiency, loss: Loss, expected_result: np.ndarray):
    arrow = Arrow(
        node="test",
        is_ingoing=True,
        conversion=conversion,
        efficiency=efficiency,
        loss=loss,
    )

    result = arrow.get_scenario_vector(mock_db(), mock_scenario_horizon(), mock_level_period(), unit="MWh")

    assert np.equal(result, expected_result).all()


@pytest.mark.parametrize(
    ("conversion", "efficiency", "loss", "expected_result"),
    [
        (
            mock_conversion(data_value=2.0),
            mock_efficiency(data_value=0.5),
            mock_loss(data_value=0.1),
            3.6,
        ),
        (
            mock_conversion(has_profile=True),
            mock_efficiency(data_value=0.5),
            mock_loss(data_value=0.1),
            1.8,
        ),
        (
            mock_conversion(has_profile=True),
            mock_efficiency(has_profile=True),
            mock_loss(data_value=0.1),
            0.9,
        ),
        (
            mock_conversion(has_profile=True),
            mock_efficiency(has_profile=True),
            mock_loss(has_profile=True),
            1.0,
        ),
        (
            mock_conversion(data_value=2.0),
            mock_efficiency(has_profile=True),
            mock_loss(data_value=0.1),
            1.8,
        ),
        (
            mock_conversion(data_value=2.0),
            mock_efficiency(has_profile=True),
            mock_loss(has_profile=True),
            2.0,
        ),
        (
            mock_conversion(has_profile=True),
            mock_efficiency(data_value=0.5),
            mock_loss(has_profile=True),
            2.0,
        ),
        (
            mock_conversion(data_value=2.0),
            mock_efficiency(data_value=0.5),
            mock_loss(has_profile=True),
            4.0,
        ),
    ],
)
def test_get_data_value(conversion: Conversion, efficiency: Efficiency, loss: Loss, expected_result: float | None):
    arrow = Arrow(node="test", is_ingoing=True, conversion=conversion, efficiency=efficiency, loss=loss)

    result = arrow.get_data_value(mock_db(), mock_scenario_horizon(), mock_level_period(), unit="MWh")

    assert result == expected_result
