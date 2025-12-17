from unittest.mock import Mock

import pytest

from framcore import Model
from framcore.querydbs import ModelDB


def _mock_model():
    model = Mock(spec=Model)
    model.get_data.return_value = dict()
    return model


def test_init_requires_at_least_one_model():
    with pytest.raises(TypeError):
        ModelDB()


def test_init_with_primary_model():
    primary_model = _mock_model()

    db = ModelDB(model=primary_model)

    assert db._models == (primary_model,)


def test_init_with_multiple_models():
    primary_model = _mock_model()
    second_model = _mock_model()
    third_model = _mock_model()

    db = ModelDB(primary_model, second_model, third_model)

    assert primary_model in db._models
    assert second_model in db._models
    assert third_model in db._models


def test_when_key_exist_in_primary_model_return_value_from_model():
    model = _mock_model()
    model.get_data.return_value = {"key": "primary_model_value"}

    db = ModelDB(model)

    assert db.has_key("key") is True
    assert db.get("key") == "primary_model_value"


def test_when_key_exist_in_any_secondary_model_return_value_from_secondary_model():
    primary_model = _mock_model()

    secondary_model1 = _mock_model()
    secondary_model1.get_data.return_value = {"key1": "secondary_model1_value"}

    secondary_model2 = _mock_model()
    secondary_model2.get_data.return_value = {"key2": "secondary_model2_value"}

    db = ModelDB(primary_model, secondary_model1, secondary_model2)

    assert db.has_key("key1") is True
    assert db.has_key("key2") is True
    assert db.get("key1") == "secondary_model1_value"
    assert db.get("key2") == "secondary_model2_value"


def test_when_key_does_not_exist_in_cache_and_any_model_raise_key_error():
    primary_model = _mock_model()
    secondary_model1 = _mock_model()
    secondary_model2 = _mock_model()

    db = ModelDB(primary_model, secondary_model1, secondary_model2)

    assert db.has_key("non_existent_key") is False

    with pytest.raises(KeyError):
        db.get("non_existent_key")


def test_get_data_returns_primary_model_data():
    primary_model = _mock_model()
    primary_model.get_data.return_value = {"key1": "primary_value"}
    secondary_model = _mock_model()
    secondary_model.get_data.return_value = {"key2": "secondary_value"}
    db = ModelDB(primary_model, secondary_model)

    data = db.get_data()

    assert data == {"key1": "primary_value"}
