from framcore.attributes import AvgFlowVolume, Cost
from framcore.components import Flow, Wind


def test_init_minimal_args():
    wind = Wind(power_node="node", max_capacity=AvgFlowVolume())

    assert wind.get_power_node() == "node"
    assert isinstance(wind.get_max_capacity(), AvgFlowVolume)
    assert isinstance(wind.get_production(), AvgFlowVolume)
    assert wind.get_voc() is None


def test_init_all_args():
    max_cap = AvgFlowVolume()
    voc = Cost(value=5.0, unit="NOK/MWh")
    production = AvgFlowVolume()

    wind = Wind(
        power_node="node2",
        max_capacity=max_cap,
        voc=voc,
        production=production,
    )

    assert wind.get_power_node() == "node2"
    assert wind.get_max_capacity() is max_cap
    assert wind.get_voc() is voc
    assert wind.get_production() is production


def test__get_simpler_components():
    wind = Wind(power_node="node", max_capacity=AvgFlowVolume())

    components = wind._get_simpler_components(base_name="Wind")

    assert "Wind_Flow" in components
    assert isinstance(components["Wind_Flow"], Flow)

def test__create_flow_with_voc():
    voc = Cost(value=10.0, unit="NOK/MWh")
    wind = Wind(power_node="node", max_capacity=AvgFlowVolume(), voc=voc)

    flow = wind._create_flow()

    assert flow is not None
    assert flow.get_main_node() == "node"
    assert flow.get_max_capacity() == wind.get_max_capacity()
    assert flow.get_volume() == wind.get_production()
    assert "VOC" in flow.get_cost_terms()
    assert flow.get_cost_terms()["VOC"] == voc
    assert flow.is_exogenous() is False

def test__create_flow_without_voc():
    max_cap = AvgFlowVolume(value=100)
    production = AvgFlowVolume(value=80)
    wind = Wind(power_node="node", max_capacity=max_cap, production=production)

    flow = wind._create_flow()

    assert flow is not None
    assert flow.get_main_node() == "node"
    assert flow.get_max_capacity() == max_cap
    assert flow.get_volume() == production
    assert flow.get_min_capacity() == max_cap
    assert flow.is_exogenous() is True
