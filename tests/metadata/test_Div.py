from unittest.mock import Mock

import pytest

from framcore.metadata import Div, Meta


def test_init_when_value_is_meta_shoud_add_to_value_set():
    meta = Mock(Meta)

    div = Div(value=meta)

    assert div.get_value() is not None
    assert len(div.get_value()) == 1
    assert meta in div.get_value()


def test_init_when_value_is_set_of_meta_shoud_add_all_to_value_set():
    meta1 = Mock(Meta)
    meta2 = Mock(Meta)
    meta_set = {meta1, meta2}

    div = Div(value=meta_set)

    assert div.get_value() is not None
    assert len(div.get_value()) == 2
    assert meta1 in div.get_value()
    assert meta2 in div.get_value()


def test_init_when_value_is_none_shoud_initialize_empty_value_set():
    div = Div(value=None)

    assert div.get_value() is not None
    assert len(div.get_value()) == 0


@pytest.mark.parametrize(
    "value",
    [
        42,
        "invalid_string",
        3.14,
        [Mock(Meta)],
        {"not_meta"},
    ],
)
def test_init_invalid_input_raises(value):
    with pytest.raises(TypeError):
        Div(value=value)


def test_set_value_with_meta_adds_to_value_set():
    meta = Mock(Meta)
    div = Div()

    div.set_value(meta)

    assert div.get_value() is not None
    assert len(div.get_value()) == 1
    assert meta in div.get_value()


def test_set_value_with_set_of_meta_adds_all_to_value_set():
    meta1 = Mock(Meta)
    meta2 = Mock(Meta)
    meta_set = {meta1, meta2}
    div = Div()

    div.set_value(meta_set)

    assert div.get_value() is not None
    assert len(div.get_value()) == 2
    assert meta1 in div.get_value()
    assert meta2 in div.get_value()


@pytest.mark.parametrize(
    "value",
    [
        42,
        "invalid_string",
        3.14,
        [Mock(Meta)],
        {"not_meta"},
        None,
    ],
)
def test_set_value_invalid_input_raises(value):
    div = Div()

    with pytest.raises(TypeError):
        div.set_value(value)


def test_combine_with_meta_adds_to_value_set():
    meta = Mock(Meta)
    div = Div()

    div.combine(meta)

    assert div.get_value() is not None
    assert len(div.get_value()) == 1
    assert meta in div.get_value()


def test_combine_with_set_of_meta_adds_all_to_value_set():
    meta1 = Mock(Meta)
    meta2 = Mock(Meta)
    meta_set = {meta1, meta2}
    div = Div()

    div.combine(meta_set)

    assert div.get_value() is not None
    assert len(div.get_value()) == 2
    assert meta1 in div.get_value()
    assert meta2 in div.get_value()


def test_combine_with_div_adds_all_to_value_set():
    meta1 = Mock(Meta)
    meta2 = Mock(Meta)
    div1 = Div(value=meta1)
    div2 = Div(value=meta2)

    div1.combine(div2)

    assert div1.get_value() is not None
    assert len(div1.get_value()) == 2
    assert meta1 in div1.get_value()
    assert meta2 in div1.get_value()
