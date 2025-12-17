from unittest.mock import Mock

import pytest

from framcore.attributes import Arrow, AvgFlowVolume, ObjectiveCoefficient, StartUpCost
from framcore.components import Flow


def test_init_minimal_args():
    flow = Flow(main_node="node1")

    assert flow._main_node == "node1"
    assert isinstance(flow._volume, AvgFlowVolume)
    assert flow._max_capacity is None
    assert flow._min_capacity is None
    assert flow._startupcost is None
    assert flow._arrow_volumes == {}
    assert flow._is_exogenous is False


def test_init_all_args():
    max_cap = AvgFlowVolume()
    min_cap = AvgFlowVolume()
    startup = Mock(spec=StartUpCost)
    volume = AvgFlowVolume()
    arrow = AvgFlowVolume()
    arrow_volumes = {arrow: AvgFlowVolume()}

    flow = Flow(
        main_node="node2",
        max_capacity=max_cap,
        min_capacity=min_cap,
        startupcost=startup,
        volume=volume,
        arrow_volumes=arrow_volumes,
        is_exogenous=True,
    )

    assert flow._main_node == "node2"
    assert flow._max_capacity is max_cap
    assert flow._min_capacity is min_cap
    assert flow._startupcost is startup
    assert flow._arrows == set()
    assert flow._cost_terms == {}
    assert flow._is_exogenous is True
    assert flow._volume is volume
    assert flow._arrow_volumes == arrow_volumes


def test_init_arrow_volumes_none():
    flow = Flow(main_node="node3", arrow_volumes=None)
    assert isinstance(flow.get_arrow_volumes(), dict)
    assert flow.get_arrow_volumes() == {}


def test_init_volume_none():
    flow = Flow(main_node="node4", volume=None)
    assert isinstance(flow.get_volume(), AvgFlowVolume)


def test_add_cost_term_adds_term():
    flow = Flow(main_node="node5")
    key = "cost1"
    cost_term = Mock(spec=ObjectiveCoefficient)

    flow.add_cost_term(key, cost_term)

    assert key in flow.get_cost_terms()
    assert flow.get_cost_terms()[key] is cost_term


def test_add_cost_term_overwrites_existing_key():
    flow = Flow(main_node="node6")
    key = "cost2"
    cost_term1 = Mock(spec=ObjectiveCoefficient)
    cost_term2 = Mock(spec=ObjectiveCoefficient)
    flow.add_cost_term(key, cost_term1)
    flow.add_cost_term(key, cost_term2)
    assert flow.get_cost_terms()[key] is cost_term2


def test_add_cost_term_invalid_key_type_raises():
    flow = Flow(main_node="node7")
    cost_term = Mock(spec=ObjectiveCoefficient)
    with pytest.raises(TypeError):
        flow.add_cost_term(123, cost_term)


def test_add_cost_term_invalid_cost_term_type_raises():
    flow = Flow(main_node="node8")
    with pytest.raises(TypeError):
        flow.add_cost_term("cost3", "not_a_cost_term")


def test_replace_node_main_node_changes():
    flow = Flow(main_node="old_node")
    flow._replace_node("old_node", "new_node")
    assert flow.get_main_node() == "new_node"


def test_replace_node_arrow_node_changes():
    flow = Flow(main_node="main_node")
    arrow = Arrow(node="old_node", is_ingoing=True)
    flow.get_arrows().add(arrow)

    flow._replace_node("old_node", "new_node")

    assert flow.get_arrows().pop().get_node() == "new_node"


def test_replace_node_main_and_arrow_node_changes_only_main():
    arrow = Arrow(node="some_node", is_ingoing=True)
    flow = Flow(main_node="old_node")
    flow.get_arrows().add(arrow)
    flow._replace_node("old_node", "new_node")

    assert flow.get_main_node() == "new_node"
    assert flow.get_arrows().pop().get_node() == "some_node"


def test_replace_node_no_match_does_nothing():
    arrow = Arrow(node="node", is_ingoing=True)
    flow = Flow(main_node="node")
    flow.get_arrows().add(arrow)
    flow._replace_node("old_node", "new_node")

    assert flow.get_main_node() == "node"
    assert flow.get_arrows().pop().get_node() == "node"


def test__get_simpler_components_returns_empty_dict():
    flow = Flow(main_node="node")
    result = flow._get_simpler_components("base")
    assert result == {}
