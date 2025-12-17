from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from framcore import Base
from framcore.metadata import Meta


class Component(Base, ABC):
    """
    Components describe the main elements in the energy system. Can have additional Attributes and Metadata.

    We have high-level and low-level Components. High-level Components, such as a HydroModule,
    can be decomposed into low-level Components like Flows and Nodes. The high-level description lets
    analysts work with recognizable domain objects, while the low-level descriptions enable generic algorithms
    that minimize code duplication and simplify data manipulation.

    Some energy market models like JulES, SpineOpt and PyPSA also have a generic description of the system,
    so this two-tier system can be used to easier adapt the dataset to their required formats.

    The method Component.get_simpler_components() is used to decompose high-level Components into low-level
    Components. This can also be used together with the utility function get_supported_components() to transform
    a set of Components into a set that only contains supported Component types.

    Result attributes are initialized in the high-level Components. When they are transferred to low-level Components,
    and the results are set by a model like JulES, the results will also appear in the high-level Components.

    Nodes, Flows and Arrows are the main building blocks in FRAM's low-level representation of energy systems.
    Node represent a point where a commodity can possibly be traded, stored or pass through.
    Movement between Nodes is represented by Flows and Arrows. Flows represent a commodity flow,
    and can have Arrows that each describe contribution of the Flow into a Node.
    The Arrows have direction to determine input or output, and parameters for the contribution of the
    Flow to the Node (conversion, efficiency and loss).
    """

    def __init__(self) -> None:
        """Set mandatory private variables."""
        self._parent: Component | None = None
        self._meta: dict[str, Meta] = dict()

    def add_meta(self, key: str, value: Meta) -> None:
        """Add metadata to component. Overwrite if already exist."""
        self._check_type(key, str)
        self._check_type(value, Meta)
        self._meta[key] = value

    def get_meta(self, key: str) -> Meta | None:
        """Get metadata from component or return None if not exist."""
        self._check_type(key, str)
        return self._meta.get(key, None)

    def get_meta_keys(self) -> Iterable[str]:
        """Get iterable with all metakeys in component."""
        return self._meta.keys()

    def get_simpler_components(
        self,
        base_name: str,
    ) -> dict[str, Component]:
        """
        Return representation of self as dict of named simpler components.

        The base_name should be unique within a model instance, and should
        be used to prefix name of all simpler components.

        Insert self as parent in each child.

        Transfer metadata to each child.
        """
        self._check_type(base_name, str)
        components = self._get_simpler_components(base_name)
        assert base_name not in components, f"base_name: {base_name} should not be in \ncomponent: {self}"
        components: dict[str, Component]
        self._check_type(components, dict)
        for name, c in components.items():
            self._check_type(name, str)
            self._check_type(c, Component)
            self._check_component_not_self(c)
            c: Component
            c._parent = self  # noqa: SLF001
        for key in self.get_meta_keys():
            value = self.get_meta(key)
            for c in components.values():
                c.add_meta(key, value)
        return components

    def get_parent(self) -> Component | None:
        """Return parent if any, else None."""
        self._check_type(self._parent, (Component, type(None)))
        self._check_component_not_self(self._parent)
        return self._parent

    def get_parents(self) -> list[Component]:
        """Return list of all parents, including self."""
        child = self
        parent = child.get_parent()
        parents = [child]
        while parent is not None:
            child = parent
            parent = child.get_parent()
            parents.append(child)
        self._check_unique_parents(parents)
        return parents

    def get_top_parent(self) -> Component:
        """Return topmost parent. (May be object self)."""
        parents = self.get_parents()
        return parents[-1]

    def replace_node(self, old: str, new: str) -> None:
        """Replace old Node with new. Not error if no match."""
        self._check_type(old, str)
        self._check_type(new, str)
        self._replace_node(old, new)

    def _check_component_not_self(self, other: Component | None) -> None:
        if not isinstance(other, Component):
            return
        if self != other:
            return
        message = f"Expected other component than {self}."
        raise TypeError(message)

    def _check_unique_parents(self, parents: list[Component]) -> None:
        if len(parents) > len(set(parents)):
            message = f"Parents for {self} are not unique."
            raise TypeError(message)

    @abstractmethod
    def _replace_node(self, old: str, new: str) -> None:
        pass

    @abstractmethod
    def _get_simpler_components(self, base_name: str) -> dict[str, Component]:
        pass
