from framcore.attributes import AvgFlowVolume, Conversion, Cost, Loss, Proportion
from framcore.components import Flow, Transmission


def test_init_minimal_required_args():
    transmission = Transmission(
        from_node="A",
        to_node="B",
        max_capacity=AvgFlowVolume(value=100),
    )

    assert transmission.get_to_node() == "B"
    assert transmission.get_from_node() == "A"
    assert transmission.get_max_capacity() == AvgFlowVolume(value=100)
    assert transmission.get_min_capacity() is None
    assert transmission.get_loss() is None
    assert transmission.get_tariff() is None
    assert transmission.get_ramp_up() is None
    assert transmission.get_ramp_down() is None
    assert isinstance(transmission.get_ingoing_volume(), AvgFlowVolume)
    assert isinstance(transmission.get_outgoing_volume(), AvgFlowVolume)


def test_init_all_args():
    transmission = Transmission(
        from_node="A",
        to_node="B",
        max_capacity=AvgFlowVolume(value=200),
        min_capacity=AvgFlowVolume(value=50),
        loss=Loss(value=0.1),
        tariff=Cost(value=5.0, unit="NOK/MWh"),
        ramp_up=Proportion(value=0.2),
        ramp_down=Proportion(value=0.3),
    )

    assert transmission.get_to_node() == "B"
    assert transmission.get_from_node() == "A"
    assert transmission.get_max_capacity() == AvgFlowVolume(value=200)
    assert transmission.get_min_capacity() == AvgFlowVolume(value=50)
    assert transmission.get_loss() == Loss(value=0.1)
    assert transmission.get_tariff() == Cost(value=5.0, unit="NOK/MWh")
    assert transmission.get_ramp_up() == Proportion(value=0.2)
    assert transmission.get_ramp_down() == Proportion(value=0.3)


def test_get_simpler_components_returns_dict_with_flow():
    transmission = Transmission(
        from_node="A",
        to_node="B",
        max_capacity=AvgFlowVolume(value=100),
    )

    result = transmission._get_simpler_components("Base")

    assert isinstance(result, dict)
    assert "Base_Flow" in result

    flow = result["Base_Flow"]
    assert isinstance(flow, Flow)


def test_replace_node_from_node():
    transmission = Transmission(
        from_node="A",
        to_node="B",
        max_capacity=AvgFlowVolume(value=100),
    )
    transmission._replace_node("A", "C")
    assert transmission.get_from_node() == "C"
    assert transmission.get_to_node() == "B"


def test_replace_node_to_node():
    transmission = Transmission(
        from_node="A",
        to_node="B",
        max_capacity=AvgFlowVolume(value=100),
    )

    transmission._replace_node("B", "D")

    assert transmission.get_from_node() == "A"
    assert transmission.get_to_node() == "D"


def test_replace_node_both_nodes():
    transmission = Transmission(
        from_node="A",
        to_node="A",
        max_capacity=AvgFlowVolume(value=100),
    )

    transmission._replace_node("A", "Z")

    assert transmission.get_from_node() == "Z"
    assert transmission.get_to_node() == "Z"


def test_replace_node_no_match():
    transmission = Transmission(
        from_node="A",
        to_node="B",
        max_capacity=AvgFlowVolume(value=100),
    )

    transmission._replace_node("X", "Y")

    assert transmission.get_from_node() == "A"
    assert transmission.get_to_node() == "B"


def test_create_flow_basic():
    transmission = Transmission(
        from_node="A",
        to_node="B",
        max_capacity=AvgFlowVolume(value=100),
    )

    flow = transmission._create_flow()

    assert isinstance(flow, Flow)
    assert flow.get_main_node() == "A"
    assert flow.get_max_capacity() == AvgFlowVolume(value=100)
    assert flow.get_volume() == transmission.get_outgoing_volume()

    # Check that there are two arrows: one outgoing, one ingoing
    arrows = list(flow.get_arrow_volumes().keys())
    assert len(arrows) == 2

    outgoing = [a for a in arrows if not a.is_ingoing() and a.get_node() == "A"]
    assert len(outgoing) == 1
    assert outgoing[0].get_conversion() == Conversion(value=1)
    assert flow.get_arrow_volumes()[outgoing[0]] == transmission.get_outgoing_volume()

    ingoing = [a for a in arrows if a.is_ingoing() and a.get_node() == "B"]
    assert len(ingoing) == 1
    assert ingoing[0].get_conversion() == Conversion(value=1)
    assert ingoing[0].get_loss() == transmission.get_loss()
    assert flow.get_arrow_volumes()[ingoing[0]] == transmission.get_ingoing_volume()


def test_create_flow_with_tariff():
    transmission = Transmission(
        from_node="A",
        to_node="B",
        max_capacity=AvgFlowVolume(value=100),
        tariff=Cost(value=3.0, unit="NOK/MWh"),
    )

    flow = transmission._create_flow()

    assert "tariff" in flow.get_cost_terms()
    assert flow.get_cost_terms()["tariff"] == Cost(value=3.0, unit="NOK/MWh")
