import pytest

from framcore.attributes import AvgFlowVolume, Conversion, Cost, Efficiency, Hours, MaxFlowVolume, Proportion, StartUpCost
from framcore.components import Flow, Thermal


def test_init_minimal_required_args():
    eff = Efficiency(value=0.4)
    t = Thermal(
        power_node="P",
        fuel_node="F",
        efficiency=eff,
        max_capacity=MaxFlowVolume(value=150),
    )
    assert t._power_node == "P"
    assert t._fuel_node == "F"
    assert t._efficiency is eff
    assert isinstance(t._production, AvgFlowVolume)
    assert isinstance(t._fuel_demand, AvgFlowVolume)
    assert t._emission_node is None
    assert t._emission_coefficient is None
    assert t._startupcost is None
    assert t._emission_demand is None


def test_init_all_args():
    eff = Efficiency(value=0.5)
    conv = Conversion(value=0.6)
    startup = StartUpCost(
        startup_cost=Cost(value=100), min_stable_load=Proportion(value=0.8), start_hours=Hours(value=5), part_load_efficiency=Efficiency(value=0.7),
    )
    maxcap = MaxFlowVolume(value=200)
    mincap = MaxFlowVolume(value=100)
    voc = Cost(value=50)
    prod = AvgFlowVolume(value=75)
    fuel_dem = AvgFlowVolume(value=80)
    emission_dem = AvgFlowVolume(value=90)

    thermal = Thermal(
        power_node="P",
        fuel_node="F",
        efficiency=eff,
        emission_node="E",
        emission_coefficient=conv,
        startupcost=startup,
        max_capacity=maxcap,
        min_capacity=mincap,
        voc=voc,
        production=prod,
        fuel_demand=fuel_dem,
        emission_demand=emission_dem,
    )

    assert thermal._power_node == "P"
    assert thermal._fuel_node == "F"
    assert thermal._efficiency is eff
    assert thermal._emission_node == "E"
    assert thermal._emission_coefficient is conv
    assert thermal._startupcost is startup
    assert thermal._max_capacity is maxcap
    assert thermal._min_capacity is mincap
    assert thermal._voc is voc
    assert thermal._production is prod
    assert thermal._fuel_demand is fuel_dem
    assert thermal._emission_demand is emission_dem


def test_init_emission_demand_autoset():
    eff = Efficiency(value=0.4)
    thermal = Thermal(power_node="P", fuel_node="F", efficiency=eff, max_capacity=MaxFlowVolume(value=150), emission_node="E")
    assert isinstance(thermal.get_emission_demand(), AvgFlowVolume)


def test_get_simpler_components_returns_flow():
    eff = Efficiency(value=0.4)
    thermal = Thermal(power_node="P", fuel_node="F", efficiency=eff, max_capacity=MaxFlowVolume(value=150))

    result = thermal._get_simpler_components("BaseName")

    assert isinstance(result, dict)
    assert "BaseName_Flow" in result

    assert isinstance(result["BaseName_Flow"], Flow)


def test_replace_node_power_node():
    eff = Efficiency(value=0.4)
    thermal = Thermal(power_node="P", fuel_node="F", efficiency=eff, max_capacity=MaxFlowVolume(value=150))

    thermal._replace_node("P", "P_new")

    assert thermal.get_power_node() == "P_new"
    assert thermal.get_fuel_node() == "F"
    assert thermal.get_emission_node() is None


def test_replace_node_fuel_node():
    eff = Efficiency(value=0.4)
    thermal = Thermal(power_node="P", fuel_node="F", efficiency=eff, max_capacity=MaxFlowVolume(value=150))

    thermal._replace_node("F", "F_new")

    assert thermal.get_fuel_node() == "F_new"
    assert thermal.get_power_node() == "P"
    assert thermal.get_emission_node() is None


def test_replace_node_emission_node():
    eff = Efficiency(value=0.4)
    thermal = Thermal(power_node="P", fuel_node="F", efficiency=eff, emission_node="E", max_capacity=MaxFlowVolume(value=150))

    thermal._replace_node("E", "E_new")

    assert thermal.get_emission_node() == "E_new"
    assert thermal.get_power_node() == "P"
    assert thermal.get_fuel_node() == "F"


def test_replace_node_invalid_node_raises():
    eff = Efficiency(value=0.4)
    thermal = Thermal(power_node="P", fuel_node="F", efficiency=eff, max_capacity=MaxFlowVolume(value=150))

    with pytest.raises(ValueError, match="^X not found in"):
        thermal._replace_node("X", "X_new")


def test_create_flow_basic():
    eff = Efficiency(value=0.4)
    maxcap = MaxFlowVolume(value=100)
    mincap = MaxFlowVolume(value=50)
    prod = AvgFlowVolume(value=75)
    fuel_dem = AvgFlowVolume(value=80)

    thermal = Thermal(
        power_node="P",
        fuel_node="F",
        efficiency=eff,
        max_capacity=maxcap,
        min_capacity=mincap,
        production=prod,
        fuel_demand=fuel_dem,
    )

    flow = thermal._create_flow()

    assert isinstance(flow, Flow)
    assert flow.get_main_node() == "P"
    assert flow.get_max_capacity() is maxcap
    assert flow.get_min_capacity() is mincap
    assert flow.get_volume() is prod

    # Check arrows
    arrow_nodes = [arrow.get_node() for arrow in flow.get_arrows()]
    assert "P" in arrow_nodes
    assert "F" in arrow_nodes

    # Check fuel arrow volume
    fuel_arrows = [arrow for arrow in flow.get_arrows() if arrow.get_node() == "F"]
    assert len(fuel_arrows) == 1
    assert flow.get_arrow_volumes()[fuel_arrows[0]] is fuel_dem


def test_create_flow_with_emission():
    eff = Efficiency(value=0.4)
    conv = Conversion(value=0.6)
    emission_dem = AvgFlowVolume(value=90)

    thermal = Thermal(
        power_node="P",
        fuel_node="F",
        efficiency=eff,
        max_capacity=MaxFlowVolume(value=100),
        emission_node="E",
        emission_coefficient=conv,
        emission_demand=emission_dem,
    )

    flow = thermal._create_flow()

    arrow_nodes = [arrow.get_node() for arrow in flow.get_arrows()]
    assert "E" in arrow_nodes

    emission_arrows = [arrow for arrow in flow.get_arrows() if arrow.get_node() == "E"]
    assert len(emission_arrows) == 1
    assert flow.get_arrow_volumes()[emission_arrows[0]] is emission_dem
    assert emission_arrows[0].get_conversion() is conv
    assert emission_arrows[0].get_efficiency() is eff


def test_create_flow_emission_demand_autoset():
    eff = Efficiency(value=0.4)
    conv = Conversion(value=0.6)
    thermal = Thermal(
        power_node="P",
        fuel_node="F",
        efficiency=eff,
        max_capacity=MaxFlowVolume(value=100),
        emission_node="E",
        emission_coefficient=conv,
    )
    flow = thermal._create_flow()
    emission_arrows = [arrow for arrow in flow.get_arrows() if arrow.get_node() == "E"]
    assert len(emission_arrows) == 1
    assert isinstance(flow.get_arrow_volumes()[emission_arrows[0]], AvgFlowVolume)


def test_create_flow_with_voc():
    eff = Efficiency(value=0.4)
    voc = Cost(value=50)

    thermal = Thermal(
        power_node="P",
        fuel_node="F",
        efficiency=eff,
        max_capacity=MaxFlowVolume(value=100),
        voc=voc,
    )
    flow = thermal._create_flow()
    assert "VOC" in flow.get_cost_terms()
    assert flow.get_cost_terms()["VOC"] is voc


def test_create_flow_is_exogenous_true():
    eff = Efficiency(value=0.4)
    maxcap = MaxFlowVolume(value=100)

    thermal = Thermal(
        power_node="P",
        fuel_node="F",
        efficiency=eff,
        max_capacity=maxcap,
        min_capacity=maxcap,
    )

    flow = thermal._create_flow()

    assert flow.is_exogenous() is True


def test_create_flow_is_exogenous_false():
    eff = Efficiency(value=0.4)
    maxcap = MaxFlowVolume(value=100)
    mincap = MaxFlowVolume(value=50)

    thermal = Thermal(
        power_node="P",
        fuel_node="F",
        efficiency=eff,
        max_capacity=maxcap,
        min_capacity=mincap,
    )

    flow = thermal._create_flow()

    assert flow.is_exogenous() is False
