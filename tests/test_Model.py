from unittest.mock import Mock

import pytest

from framcore.components import Component
from framcore.curves import Curve
from framcore.expressions import Expr
from framcore.Model import Model, ModelDict
from framcore.timevectors import TimeVector


def test_init_model_basic():
    model = Model()

    assert isinstance(model.get_data(), ModelDict)
    assert len(model.get_data()) == 0

    counts = model.get_content_counts()
    for concept_counter in counts.values():
        assert sum(concept_counter.values()) == 0


def test_add_valid_data_items_to_model():
    model = Model()
    model.get_data()["component"] = Mock(Component)
    model.get_data()["expr"] = Mock(Expr)
    model.get_data()["curve"] = Mock(Curve)
    model.get_data()["timevector"] = Mock(TimeVector)

    counts = model.get_content_counts()
    assert len(counts["components"]) == 1
    assert len(counts["timevectors"]) == 1
    assert len(counts["curves"]) == 1
    assert len(counts["expressions"]) == 1


def test_add_data_with_invalid_key_raise_type_error():
    model = Model()

    with pytest.raises(TypeError):
        model.get_data()[123] = Mock(Component)

@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("key1", 123),
        ("key5", 3.14),
        ("key2", "some_string"),
        ("key3", []),
        ("key4", {}),
    ],
)
def test_add_invalid_data_type_raises_type_error(key, value):
    model = Model()
    with pytest.raises(TypeError):
        model.get_data()[key] = value

def test_disaggregate():
    model = Model()

    mock_aggregator_1 = Mock()
    model._aggregators.append(mock_aggregator_1)

    mock_aggregator_2 = Mock()
    model._aggregators.append(mock_aggregator_2)

    model.disaggregate()
    mock_aggregator_1.disaggregate.assert_called_once_with(model)
    mock_aggregator_2.disaggregate.assert_called_once_with(model)

    # After disaggregation, the aggregators list should be empty
    assert len(model._aggregators) == 0
