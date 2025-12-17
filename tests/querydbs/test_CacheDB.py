from unittest.mock import Mock

import pytest

from framcore import Model
from framcore.querydbs import CacheDB


def _mock_model():
    model = Mock(spec=Model)
    model.get_data.return_value = dict()
    return model


def test_init_requires_at_least_one_model():
    with pytest.raises(TypeError):
        CacheDB()


def test_init_with_primary_model():
    primary_model = _mock_model()

    db = CacheDB(model=primary_model)

    assert db._models == (primary_model,)


def test_init_with_multiple_models():
    primary_model = _mock_model()
    second_model = _mock_model()
    third_model = _mock_model()

    db = CacheDB(primary_model, second_model, third_model)

    assert primary_model in db._models
    assert second_model in db._models
    assert third_model in db._models


def test_min_elapsed_seconds_setting():
    db = CacheDB(_mock_model())

    db.set_min_elapsed_seconds(0.05)

    assert db.get_min_elapsed_seconds() == 0.05


@pytest.mark.parametrize(
    "invalid_value",
    [
        "string",
        10,
        None,
        [],
        {},
    ],
)
def test_set_min_elapsed_seconds_invalid_type_raises_type_error(invalid_value):
    db = CacheDB(_mock_model())

    with pytest.raises(TypeError):
        db.set_min_elapsed_seconds(invalid_value)


def test_set_min_elapsed_seconds_negative_value_raises_value_error():
    db = CacheDB(_mock_model())

    with pytest.raises(ValueError, match=".+"):
        db.set_min_elapsed_seconds(-0.1)


def test_when_key_exist_in_cache_return_value_from_cache():
    db = CacheDB(_mock_model())
    db.put(key="key", value="some_value", elapsed_seconds=100.0)

    assert db.has_key("key") is True
    assert db.get("key") == "some_value"


def test_when_key_exist_in_primary_model_return_value_from_model():
    model = _mock_model()
    model.get_data.return_value = {"key": "primary_model_value"}

    db = CacheDB(model)

    assert db.has_key("key") is True
    assert db.get("key") == "primary_model_value"


def test_when_key_exist_in_any_secondary_model_return_value_from_secondary_model():
    primary_model = _mock_model()

    secondary_model1 = _mock_model()
    secondary_model1.get_data.return_value = {"key1": "secondary_model1_value"}

    secondary_model2 = _mock_model()
    secondary_model2.get_data.return_value = {"key2": "secondary_model2_value"}

    db = CacheDB(primary_model, secondary_model1, secondary_model2)

    assert db.has_key("key1") is True
    assert db.has_key("key2") is True
    assert db.get("key1") == "secondary_model1_value"
    assert db.get("key2") == "secondary_model2_value"


def test_when_key_does_not_exist_in_cache_and_any_model_raise_key_error():
    primary_model = _mock_model()
    secondary_model1 = _mock_model()
    secondary_model2 = _mock_model()

    db = CacheDB(primary_model, secondary_model1, secondary_model2)

    assert db.has_key("non_existent_key") is False

    with pytest.raises(KeyError):
        db.get("non_existent_key")


def test_put_does_not_cache_value_if_elapsed_seconds_below_threshold():
    db = CacheDB(_mock_model())
    db.set_min_elapsed_seconds(1.0)

    db.put(key="key", value="some_value", elapsed_seconds=0.5)

    assert db.has_key("key") is False


def test_get_data_returns_primary_model_data():
    primary_model = _mock_model()
    primary_model.get_data.return_value = {"key1": "primary_value"}
    secondary_model = _mock_model()
    secondary_model.get_data.return_value = {"key2": "secondary_value"}
    db = CacheDB(primary_model, secondary_model)

    data = db.get_data()

    assert data == {"key1": "primary_value"}
