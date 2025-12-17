from __future__ import annotations

from typing import TYPE_CHECKING

from framcore.attributes import Price, ShadowPrice, Storage
from framcore.components import Component

if TYPE_CHECKING:
    from framcore.loaders import Loader


class Node(Component):
    """
    Represents a point in the energy system where a commodity can possibly be traded, stored or pass through.

    A node is characterized by the commodity it handles, its price, and optionally storage capabilities. If the
    node is exogenous, the commodity can be bought and sold at a fixed price determined by the user.
    If the node is endogenous, the price is determined by the market dynamics at the Node.

    Nodes, Flows and Arrows are the main building blocks in FRAM's low-level representation of energy systems.
    Movement between Nodes is represented by Flows and Arrows. Flows represent a commodity flow,
    and can have Arrows that each describe contribution of the Flow into a Node.
    The Arrows have direction to determine input or output,
    and parameters for the contribution of the Flow to the Node (conversion, efficiency and loss).

    """

    def __init__(
        self,
        commodity: str,
        is_exogenous: bool = False,  # TODO
        price: ShadowPrice | None = None,
        storage: Storage | None = None,
    ) -> None:
        """
        Initialize the Node class.

        Args:
            commodity (str): Commodity at the Node. Power/electricity, gas, heat, etc.
            is_exogenous (bool, optional): Flag used to signal Solvers whether they should simulate the node endogenously or use the pre-set price.
                                           Defaults to False.
            price (ShadowPrice | None): Actual, calculated price of Commodity in this Node for each moment of simulation. Defaulta to None.
            storage (Storage | None, optional): The amount of the Commodity stored on this Node. Defaults to None.

        """
        super().__init__()
        self._check_type(commodity, str)
        self._check_type(is_exogenous, bool)
        self._check_type(price, (ShadowPrice, type(None)))
        self._check_type(storage, (Storage, type(None)))

        self._commodity = commodity
        self._is_exogenous = is_exogenous

        self._storage = storage

        if price is None:
            price = Price()

        self._price: Price = price

    def set_exogenous(self) -> None:
        """Set the Node to be exogenous."""
        self._check_type(self._is_exogenous, bool)
        self._is_exogenous = True

    def set_endogenous(self) -> None:
        """Set the Node to be endogenous."""
        self._check_type(self._is_exogenous, bool)
        self._is_exogenous = False

    def is_exogenous(self) -> bool:
        """Return True if Node is exogenous (i.e. has fixed prices determined outside the model) else False."""
        return self._is_exogenous

    def get_price(self) -> ShadowPrice:
        """Return price."""
        return self._price

    def get_storage(self) -> Storage | None:
        """Get Storage if any."""
        return self._storage

    def get_commodity(self) -> str:
        """Return commodity."""
        return self._commodity

    def add_loaders(self, loaders: set[Loader]) -> None:
        """Add loaders stored in attributes to loaders."""
        from framcore.utils import add_loaders_if

        add_loaders_if(loaders, self.get_price())
        add_loaders_if(loaders, self.get_storage())

    def _replace_node(self, old: str, new: str) -> None:
        return None

    def _get_simpler_components(self, _: str) -> dict[str, Component]:
        return dict()
