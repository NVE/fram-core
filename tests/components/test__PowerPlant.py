from framcore.attributes import AvgFlowVolume, Cost
from framcore.components import Component
from framcore.components._PowerPlant import _PowerPlant


class DummyPowerPlant(_PowerPlant):
    def __init__(  # noqa: D107
        self,
        power_node: str,
        max_capacity: AvgFlowVolume,
        min_capacity: AvgFlowVolume | None = None,
        voc: Cost | None = None,
        production: AvgFlowVolume | None = None,
    ) -> None:
        super().__init__(
            power_node=power_node,
            max_capacity=max_capacity,
            min_capacity=min_capacity,
            voc=voc,
            production=production,
        )

    def _get_simpler_components(self, base_name: str) -> dict[str, Component]:
        return super()._get_simpler_components(base_name)


def test_init_minimal_required_args():
    power_plant = DummyPowerPlant(
        power_node="node",
        max_capacity=AvgFlowVolume(value=100.0, unit="MW"),
    )

    assert power_plant.get_power_node() == "node"
    assert power_plant.get_max_capacity() == AvgFlowVolume(value=100.0, unit="MW")
    assert power_plant.get_min_capacity() is None
    assert power_plant.get_voc() is None
    assert isinstance(power_plant.get_production(), AvgFlowVolume)


def test_init_with_all_args():
    power_plant = DummyPowerPlant(
        power_node="node",
        max_capacity=AvgFlowVolume(value=100.0, unit="MW"),
        min_capacity=AvgFlowVolume(value=10.0, unit="MW"),
        voc=Cost(value=5.0, unit="NOK/MWh"),
        production=AvgFlowVolume(value=50.0, unit="MWh"),
    )

    assert power_plant.get_power_node() == "node"
    assert power_plant.get_max_capacity() == AvgFlowVolume(value=100.0, unit="MW")
    assert power_plant.get_min_capacity() == AvgFlowVolume(value=10.0, unit="MW")
    assert power_plant.get_voc() == Cost(value=5.0, unit="NOK/MWh")
    assert power_plant.get_production() == AvgFlowVolume(value=50.0, unit="MWh")


def test__replace_node():
    power_plant = DummyPowerPlant(
        power_node="old_node",
        max_capacity=AvgFlowVolume(value=100.0, unit="MW"),
    )

    power_plant._replace_node("old_node", "new_node")

    assert power_plant.get_power_node() == "new_node"
