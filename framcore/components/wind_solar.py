from framcore.attributes import Arrow, AvgFlowVolume, Conversion, Cost, FlowVolume
from framcore.components import Flow
from framcore.components._PowerPlant import _PowerPlant


class _WindSolar(_PowerPlant):
    """
    Wind and Solar class component representing a wind and solar power plant. Subclass of PowerPlant.

    This class models a wind or solar power plant with various attributes inherited from the parent class PowerPlant.
    """

    def __init__(
        self,
        power_node: str,
        max_capacity: FlowVolume,
        voc: Cost | None = None,
        production: AvgFlowVolume | None = None,
    ) -> None:
        """
        Initialize the Wind and Solar class.

        Args:
            power_node (str): Reference to a power Node to produce to.
            max_capacity (FlowVolume): Maximum capacity.
            voc (Cost | None, optional): Variable operational costs. Defaults to None.
            production (AvgFlowVolume | None, optional): Actual production. Defaults to None.

        """
        super().__init__(
            power_node=power_node,
            max_capacity=max_capacity,
            min_capacity=None,
            voc=voc,
            production=production,
        )

    """Implementation of Component interface"""

    def _get_simpler_components(self, base_name: str) -> dict[str, Flow]:
        return {base_name + "_Flow": self._create_flow()}

    def _create_flow(self) -> Flow:
        flow = Flow(
            main_node=self._power_node,
            max_capacity=self._max_capacity,
            volume=self._production,
        )

        flow.add_arrow(Arrow(node=self._power_node, is_ingoing=True, conversion=Conversion(value=1)))

        if self._voc:
            flow.add_cost_term("VOC", self._voc)
        else:
            flow.set_min_capacity(self._max_capacity)
            flow.set_exogenous()

        return flow


class Wind(_WindSolar):
    """
    Wind power component.

    Has attributes for power node, capacity, variable operation cost, and production.

    Compatible with WindSolarAggregator.
    """

    pass


class Solar(_WindSolar):
    """
    Solar power component.

    Has attributes for power node, capacity, variable operation cost, and production.

    Compatible with WindSolarAggregator.
    """

    pass
