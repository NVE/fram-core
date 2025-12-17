from framcore.attributes import (
    AvgFlowVolume,
    Conversion,
    Cost,
    FlowVolume,
    HydroBypass,
    HydroGenerator,
    HydroPump,
    HydroReservoir,
    MaxFlowVolume,
    StockVolume,
    WaterValue,
)
from framcore.components import HydroModule


def hydro_pump() -> HydroPump:
    return HydroPump(
        power_node="power_node_1", from_module="hydro_module_4", to_module="hydro_module_5", energy_equivalent=Conversion(), water_capacity=MaxFlowVolume(),
    )


def hydro_generator() -> HydroGenerator:
    return HydroGenerator(power_node="power_node_1", energy_equivalent=Conversion())


def test_init_defaults():
    module = HydroModule()

    assert module._release_to is None
    assert module._release_capacity is None
    assert module._generator is None
    assert module._pump is None
    assert module._inflow is None
    assert module._reservoir is None
    assert module._hydraulic_coupling == 0
    assert module._bypass is None
    assert module._spill_to is None
    assert module._commodity == "Hydro"

    assert isinstance(module._water_value, WaterValue)
    assert isinstance(module._release_volume, AvgFlowVolume)
    assert isinstance(module._spill_volume, AvgFlowVolume)


def test_init_with_all_args():
    module = HydroModule(
        release_to="hydro_module_2",
        release_capacity=MaxFlowVolume(value=100.0, unit="m3/s"),
        generator=hydro_generator(),
        pump=hydro_pump(),
        inflow=AvgFlowVolume(),
        reservoir=HydroReservoir(capacity=StockVolume()),
        hydraulic_coupling=2,
        bypass=HydroBypass(to_module="hydro_module_6"),
        spill_to="hydro_module_3",
        commodity="Water",
        water_value=WaterValue(),
        release_volume=AvgFlowVolume(),
        spill_volume=AvgFlowVolume(),
    )

    assert module._release_to == "hydro_module_2"
    assert isinstance(module._release_capacity, FlowVolume)
    assert isinstance(module._generator, HydroGenerator)
    assert isinstance(module._pump, HydroPump)
    assert isinstance(module._inflow, AvgFlowVolume)
    assert isinstance(module._reservoir, HydroReservoir)
    assert module._hydraulic_coupling == 2
    assert isinstance(module._bypass, HydroBypass)
    assert module._spill_to == "hydro_module_3"
    assert module._commodity == "Water"
    assert isinstance(module._water_value, WaterValue)
    assert isinstance(module._release_volume, AvgFlowVolume)
    assert isinstance(module._spill_volume, AvgFlowVolume)


def test_replace_node_with_pump_and_generator(monkeypatch):
    pump = hydro_pump()
    generator = hydro_generator()
    module = HydroModule(pump=pump, generator=generator)

    module._replace_node("power_node_1", "power_node_2")

    assert pump.get_power_node() == "power_node_2"
    assert generator.get_power_node() == "power_node_2"


def test_replace_node_only_pump():
    pump = hydro_pump()
    module = HydroModule(pump=pump)

    module._replace_node("power_node_1", "power_node_2")
    assert pump.get_power_node() == "power_node_2"


def test_replace_node_only_generator():
    generator = hydro_generator()
    module = HydroModule(generator=generator)

    module._replace_node("power_node_1", "power_node_2")
    assert generator.get_power_node() == "power_node_2"


def test_replace_node_no_match():
    pump = hydro_pump()
    generator = hydro_generator()
    module = HydroModule(pump=pump, generator=generator)

    module._replace_node("power_node", "power_node_2")

    assert pump.get_power_node() == "power_node_1"
    assert generator.get_power_node() == "power_node_1"


def test_get_simpler_components_with_minimal_args():
    module = HydroModule()
    components = module._get_simpler_components("hydro_module")

    assert "hydro_module_node" in components
    assert "hydro_module_release_flow" in components
    assert "hydro_module_spill_flow" in components
    assert "hydro_module_inflow_flow" not in components
    assert "hydro_module_bypass_flow" not in components
    assert "hydro_module_pump_flow" not in components


def test_get_simpler_components_with_inflow():
    module = HydroModule(inflow=AvgFlowVolume())
    components = module._get_simpler_components("hydro_module")

    assert "hydro_module_inflow_flow" in components


def test_get_simpler_components_with_bypass():
    module = HydroModule(bypass=HydroBypass(to_module="hydro_module"))
    components = module._get_simpler_components("hydro_module")

    assert "hydro_module_bypass_flow" in components


def test_get_simpler_components_with_pump():
    module = HydroModule(pump=hydro_pump())
    components = module._get_simpler_components("hydro_module")

    assert "hydro_module_pump_flow" in components


def test_get_simpler_components_with_all_args():
    module = HydroModule(
        inflow=AvgFlowVolume(),
        bypass=HydroBypass(to_module="hydro_module"),
        pump=hydro_pump(),
    )
    components = module._get_simpler_components("hydro_module")

    assert "hydro_module_node" in components
    assert "hydro_module_release_flow" in components
    assert "hydro_module_spill_flow" in components
    assert "hydro_module_inflow_flow" in components
    assert "hydro_module_bypass_flow" in components
    assert "hydro_module_pump_flow" in components


def test_create_hydro_node_defaults():
    module = HydroModule()

    node = module._create_hydro_node()

    assert node.get_commodity() == "Hydro"
    assert isinstance(node.get_price(), WaterValue)
    assert node.get_storage() is None


def test_create_hydro_node_with_all_args():
    reservoir = HydroReservoir(capacity=StockVolume())
    water_value = WaterValue()
    module = HydroModule(
        commodity="Water",
        reservoir=reservoir,
        water_value=water_value,
    )

    node = module._create_hydro_node()

    assert node.get_commodity() == "Water"
    assert node.get_price() is water_value
    assert node.get_storage() is reservoir


def test_create_hydro_node_with_custom_commodity():
    module = HydroModule(commodity="CustomCommodity")
    node = module._create_hydro_node()
    assert node.get_commodity() == "CustomCommodity"


def test_create_hydro_node_with_none_water_value_and_reservoir():
    module = HydroModule(water_value=None, reservoir=None)

    node = module._create_hydro_node()

    assert isinstance(node.get_price(), WaterValue)
    assert node.get_storage() is None


def test_create_release_flow_defaults():
    module = HydroModule()

    flow = module._create_release_flow("hydro_module_2_node")

    assert flow.get_main_node() == "hydro_module_2_node"
    assert flow.get_max_capacity() is None
    assert flow.get_volume() == module.get_release_volume()
    assert flow.is_exogenous() is False

    arrows = flow.get_arrows()
    assert any(a.get_node() == "hydro_module_2_node" and not a.is_ingoing() for a in arrows)
    assert len(arrows) == 1  # Only outgoing arrow by default


def test_create_release_flow_with_release_to():
    module = HydroModule(release_to="hydro_module")
    flow = module._create_release_flow("hydro_module_2_node")

    arrows = flow.get_arrows()
    assert len(arrows) == 2
    assert any(a.get_node() == "hydro_module_node" and a.is_ingoing() for a in arrows)
    assert any(a.get_node() == "hydro_module_2_node" and not a.is_ingoing() for a in arrows)


def test_create_release_flow_with_generator():
    generator = hydro_generator()
    generator.set_voc(Cost())
    module = HydroModule(generator=generator)

    flow = module._create_release_flow("hydro_module_node")

    arrows = flow.get_arrows()
    assert any(a.get_node() == "hydro_module_node" and not a.is_ingoing() for a in arrows)
    assert any(a.get_node() == generator.get_power_node() and a.is_ingoing() for a in arrows)
    assert len(arrows) == 2

    arrow_volumes = flow.get_arrow_volumes()
    production_arrow = next(a for a in arrows if a.get_node() == generator.get_power_node())
    assert isinstance(arrow_volumes[production_arrow], FlowVolume)
    assert "VOC" in flow.get_cost_terms()


def test_create_release_flow_with_release_to_and_generator():
    generator = hydro_generator()
    module = HydroModule(release_to="hydro_module_2", generator=generator)
    flow = module._create_release_flow("hydro_module_node")

    arrows = flow.get_arrows()
    assert any(a.get_node() == "hydro_module_node" and not a.is_ingoing() for a in arrows)
    assert any(a.get_node() == "hydro_module_2_node" and a.is_ingoing() for a in arrows)
    assert any(a.get_node() == generator.get_power_node() and a.is_ingoing() for a in arrows)
    assert len(arrows) == 3


def test_create_release_flow_with_custom_capacity_and_volume():
    capacity = AvgFlowVolume()
    volume = AvgFlowVolume()
    module = HydroModule(release_capacity=capacity, release_volume=volume)
    flow = module._create_release_flow("hydro_module_node")

    assert flow.get_max_capacity() == capacity
    assert flow.get_volume() == volume


def test_create_spill_flow_defaults():
    module = HydroModule(spill_volume=AvgFlowVolume(value=50.0, unit="m3/s"))

    flow = module._create_spill_flow("hydro_module_node")

    assert flow.get_main_node() == "hydro_module_node"
    assert flow.get_max_capacity() is None
    assert flow.get_volume() == module.get_spill_volume()

    arrows = flow.get_arrows()

    assert len(arrows) == 1

    assert any(a.get_node() == "hydro_module_node" and not a.is_ingoing() for a in arrows)


def test_create_spill_flow_with_spill_to():
    module = HydroModule(spill_to="hydro_module_2")
    flow = module._create_spill_flow("hydro_module_node")

    arrows = flow.get_arrows()

    assert len(arrows) == 2

    assert any(a.get_node() == "hydro_module_node" and not a.is_ingoing() for a in arrows)
    assert any(a.get_node() == "hydro_module_2_node" and a.is_ingoing() for a in arrows)


def test_create_bypass_flow_defaults():
    bypass = HydroBypass(to_module=None, capacity=AvgFlowVolume(value=75.0, unit="m3/s"))
    module = HydroModule(bypass=bypass)

    flow = module._create_bypass_flow("hydro_module_node")

    assert flow.get_main_node() == "hydro_module_node"
    assert flow.get_max_capacity() == bypass.get_capacity()
    assert flow.get_volume() == bypass.get_volume()
    assert flow.is_exogenous() is False

    arrows = flow.get_arrows()

    assert len(arrows) == 1
    assert any(a.get_node() == "hydro_module_node" and not a.is_ingoing() for a in arrows)


def test_create_bypass_flow_with_to_module():
    bypass = HydroBypass(to_module="hydro_module_2")
    module = HydroModule(bypass=bypass)
    flow = module._create_bypass_flow("hydro_module_node")

    arrows = flow.get_arrows()

    assert len(arrows) == 2
    assert any(a.get_node() == "hydro_module_node" and not a.is_ingoing() for a in arrows)
    assert any(a.get_node() == "hydro_module_2_node" and a.is_ingoing() for a in arrows)


def test_create_inflow_flow_defaults():
    module = HydroModule(inflow=AvgFlowVolume(value=10.0, unit="m3/s"))

    flow = module._create_inflow_flow("hydro_module_node")

    assert flow.get_main_node() == "hydro_module_node"
    assert flow.get_max_capacity() is None
    assert flow.get_volume() == module.get_inflow()
    assert flow.is_exogenous() is True

    arrows = flow.get_arrows()
    assert len(arrows) == 1
    assert any(a.get_node() == "hydro_module_node" and a.is_ingoing() for a in arrows)


def test_create_pump_flow_basic():
    pump = hydro_pump()
    module = HydroModule(pump=pump)

    flow = module._create_pump_flow("hydro_module_node")

    assert flow.get_main_node() == "hydro_module_node"
    assert flow.get_max_capacity() == pump.get_water_capacity()
    assert flow.get_volume() == pump.get_water_consumption()
    assert flow.is_exogenous() is False

    arrows = flow.get_arrows()
    arrow_nodes = [a.get_node() for a in arrows]
    assert pump.get_to_module() + "_node" in arrow_nodes
    assert pump.get_from_module() + "_node" in arrow_nodes
    assert pump.get_power_node() in arrow_nodes

    # Check directions
    assert any(a.get_node() == pump.get_to_module() + "_node" and a.is_ingoing() for a in arrows)
    assert any(a.get_node() == pump.get_from_module() + "_node" and not a.is_ingoing() for a in arrows)
    assert any(a.get_node() == pump.get_power_node() and not a.is_ingoing() for a in arrows)

    # Check conversion values
    for a in arrows:
        if a.get_node() == pump.get_power_node():
            assert a.get_conversion() == pump.get_energy_equivalent()


def test_create_pump_flow_arrow_volumes():
    pump = hydro_pump()
    module = HydroModule(pump=pump)

    flow = module._create_pump_flow("hydro_module_node")

    arrow_volumes = flow.get_arrow_volumes()

    pump_arrow = next(a for a in flow.get_arrows() if a.get_node() == pump.get_power_node())
    assert pump_arrow in arrow_volumes
    assert arrow_volumes[pump_arrow] == pump.get_power_consumption()
