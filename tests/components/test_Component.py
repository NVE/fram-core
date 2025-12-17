import pytest

from framcore.components import Component
from framcore.metadata import Meta


class DummyMeta(Meta):
    def get_value(self) -> None:
        return None

    def set_value(self, value: None) -> None:
        pass

    def combine(self, other: Meta) -> Meta | None:
        return None

    def get_fingerprint(self) -> str:
        return "dummy_fingerprint"


class DummyComponent(Component):
    def _replace_node(self, old: str, new: str) -> None:
        pass

    def _get_simpler_components(self, base_name: str) -> dict[str, Component]:
        return {}


def test_add_meta_adds_new_key():
    comp = DummyComponent()
    meta = DummyMeta()
    comp.add_meta("key1", meta)
    assert comp._meta["key1"] is meta


def test_add_meta_overwrites_existing_key():
    comp = DummyComponent()
    meta1 = DummyMeta()
    meta2 = DummyMeta()
    comp.add_meta("key1", meta1)
    comp.add_meta("key1", meta2)
    assert comp._meta["key1"] is meta2


def test_add_meta_invalid_key_type_raises():
    comp = DummyComponent()
    meta = DummyMeta()
    with pytest.raises(TypeError):
        comp.add_meta(123, meta)  # key is not str


def test_add_meta_invalid_value_type_raises():
    comp = DummyComponent()
    with pytest.raises(TypeError):
        comp.add_meta("key1", "not_a_meta")  # value is not Meta


def test_get_simpler_components_returns_dict_with_correct_keys_and_values():
    class ChildComponent(DummyComponent):
        pass

    class ParentComponent(DummyComponent):
        def _get_simpler_components(self, base_name: str) -> dict[str, Component]:
            return {
                f"{base_name}_child1": ChildComponent(),
                f"{base_name}_child2": ChildComponent(),
            }

    parent = ParentComponent()
    meta = DummyMeta()
    parent.add_meta("meta_key", meta)

    components = parent.get_simpler_components("base")

    assert isinstance(components, dict)
    assert set(components.keys()) == {"base_child1", "base_child2"}

    for child in components.values():
        assert isinstance(child, DummyComponent)
        assert child._parent is parent
        assert child.get_meta("meta_key") is meta


def test_get_simpler_components_base_name_in_components_raises_assertion():
    class FaultyComponent(DummyComponent):
        def _get_simpler_components(self, base_name: str) -> dict[str, Component]:
            # Intentionally include base_name as a key
            return {base_name: DummyComponent()}

    comp = FaultyComponent()
    with pytest.raises(AssertionError):
        comp.get_simpler_components("base_name")


def test_get_simpler_components_invalid_base_name_type_raises():
    comp = DummyComponent()
    with pytest.raises(TypeError):
        comp.get_simpler_components(123)  # base_name is not str


def test_get_simpler_components_invalid_component_type_raises():
    class FaultyComponent(DummyComponent):
        def _get_simpler_components(self, base_name: str) -> dict[str, Component]:
            # Return a dict with a value not of type Component
            return {"child": "not_a_component"}

    comp = FaultyComponent()
    with pytest.raises(TypeError):
        comp.get_simpler_components("base")


def test_get_simpler_components_child_is_self_raises():
    class FaultyComponent(DummyComponent):
        def _get_simpler_components(self, base_name: str) -> dict[str, Component]:
            # Return a dict with self as a child
            return {"child": self}

    comp = FaultyComponent()
    with pytest.raises(TypeError):
        comp.get_simpler_components("base")


def test_get_parent_returns_none_when_no_parent():
    comp = DummyComponent()
    assert comp.get_parent() is None


def test_get_parent_returns_parent_when_set():
    parent = DummyComponent()
    child = DummyComponent()
    child._parent = parent
    assert child.get_parent() is parent


def test_get_parent_invalid_type_raises():
    comp = DummyComponent()
    comp._parent = "not_a_component_or_none"
    with pytest.raises(TypeError):
        comp.get_parent()


def test_get_parent_self_as_parent_raises():
    comp = DummyComponent()
    comp._parent = comp
    with pytest.raises(TypeError):
        comp.get_parent()


def test_get_parents_returns_self_when_no_parent():
    comp = DummyComponent()
    assert comp.get_parents() == [comp]


def test_get_parents_returns_chain_of_parents():
    top = DummyComponent()
    mid = DummyComponent()
    bottom = DummyComponent()
    mid._parent = top
    bottom._parent = mid
    assert bottom.get_parents() == [bottom, mid, top]


def test_get_parents_parent_chain_with_non_component_parent_raises():
    comp = DummyComponent()
    comp._parent = "not_a_component"
    with pytest.raises(TypeError):
        comp.get_parents()


def test_get_parents_parent_chain_with_self_as_parent_raises():
    comp = DummyComponent()
    comp._parent = comp
    with pytest.raises(TypeError):
        comp.get_parents()


def test_get_top_parent_returns_self_when_no_parent():
    comp = DummyComponent()
    assert comp.get_top_parent() is comp


def test_get_top_parent_returns_topmost_parent_in_chain():
    top = DummyComponent()
    mid = DummyComponent()
    bottom = DummyComponent()
    mid._parent = top
    bottom._parent = mid
    assert bottom.get_top_parent() is top


def test_replace_node_invalid_old_type_raises():
    comp = DummyComponent()
    with pytest.raises(TypeError):
        comp.replace_node(123, "new_node")  # old is not str


def test_replace_node_invalid_new_type_raises():
    comp = DummyComponent()
    with pytest.raises(TypeError):
        comp.replace_node("old_node", 456)  # new is not str


def test__check_component_not_self_with_none_does_not_raise():
    comp = DummyComponent()
    comp._check_component_not_self(None)


def test__check_component_not_self_with_other_component_does_not_raise():
    comp1 = DummyComponent()
    comp2 = DummyComponent()
    comp1._check_component_not_self(comp2)


def test__check_component_not_self_with_self_raises():
    comp = DummyComponent()
    with pytest.raises(TypeError, match="Expected other component than"):
        comp._check_component_not_self(comp)


def test__check_component_not_self_with_non_component_type_does_not_raise():
    comp = DummyComponent()
    comp._check_component_not_self("not_a_component")


def test__check_unique_parents_with_unique_parents_does_not_raise():
    comp1 = DummyComponent()
    comp2 = DummyComponent()
    comp3 = DummyComponent()
    parents = [comp1, comp2, comp3]
    comp1._check_unique_parents(parents)  # Should not raise


def test__check_unique_parents_with_duplicate_parents_raises():
    comp1 = DummyComponent()
    comp2 = DummyComponent()
    parents = [comp1, comp2, comp1]  # comp1 appears twice
    with pytest.raises(TypeError, match="Parents for"):
        comp1._check_unique_parents(parents)


def test__check_unique_parents_with_empty_list_does_not_raise():
    comp = DummyComponent()
    comp._check_unique_parents([])  # Should not raise
