"""Module to test the Demand class and its associated pa.DataFrameModel classes."""

import re

import pytest

from framcore.attributes import AvgFlowVolume, ElasticDemand, Elasticity, Price, ReservePrice
from framcore.components import Demand, Flow


def test_init_condition_reserve_price_and_elastic_demand() -> None:
    with pytest.raises(ValueError, match=re.escape("Cannot have 'reserve_price' and 'elastic_demand' at the same time.")):
        Demand(
            node="node",
            elastic_demand=ElasticDemand(
                price_elasticity=Elasticity(),
                min_price=Price(value=2.0, unit="NOK/MWh"),
                normal_price=Price(value=5.0, unit="NOK/MWh"),
                max_price=Price(value=10.0, unit="NOK/MWh"),
            ),
            reserve_price=ReservePrice(value=10.0, unit="NOK/MWh"),
        )


def test_init_default_consumption_is_avg_flow_volume() -> None:
    demand = Demand(node="node")
    assert isinstance(demand.get_consumption(), type(AvgFlowVolume()))


def test_set_reserve_price_sets_value_when_no_elastic_demand():
    demand = Demand(node="node")
    reserve_price = ReservePrice(value=10.0, unit="NOK/MWh")
    demand.set_reserve_price(reserve_price)
    assert demand.get_reserve_price() == reserve_price


def test_set_reserve_price_sets_none():
    demand = Demand(node="node")
    demand.set_reserve_price(None)
    assert demand.get_reserve_price() is None


def test_set_reserve_price_raises_when_elastic_demand_is_set():
    elastic_demand = ElasticDemand(
        price_elasticity=Elasticity(),
        min_price=Price(value=2.0, unit="NOK/MWh"),
        normal_price=Price(value=5.0, unit="NOK/MWh"),
        max_price=Price(value=10.0, unit="NOK/MWh"),
    )
    demand = Demand(node="node", elastic_demand=elastic_demand)
    reserve_price = ReservePrice(value=10.0, unit="NOK/MWh")
    with pytest.raises(ValueError, match="Cannot set reserve_price when elastic_demand is not None."):
        demand.set_reserve_price(reserve_price)


def test_set_reserve_price_accepts_none_when_elastic_demand_is_set():
    elastic_demand = ElasticDemand(
        price_elasticity=Elasticity(),
        min_price=Price(value=2.0, unit="NOK/MWh"),
        normal_price=Price(value=5.0, unit="NOK/MWh"),
        max_price=Price(value=10.0, unit="NOK/MWh"),
    )
    demand = Demand(node="node", elastic_demand=elastic_demand)
    demand.set_reserve_price(None)
    assert demand.get_reserve_price() is None


def test_set_reserve_price_type_check():
    demand = Demand(node="node")
    with pytest.raises(TypeError):
        demand.set_reserve_price("not_a_reserve_price")


def test_set_elastic_demand_sets_value_when_no_reserve_price():
    demand = Demand(node="node")
    elastic_demand = ElasticDemand(
        price_elasticity=Elasticity(),
        min_price=Price(value=2.0, unit="NOK/MWh"),
        normal_price=Price(value=5.0, unit="NOK/MWh"),
        max_price=Price(value=10.0, unit="NOK/MWh"),
    )
    demand.set_elastic_demand(elastic_demand)
    assert demand.get_elastic_demand() == elastic_demand


def test_set_elastic_demand_sets_none():
    demand = Demand(node="node")
    demand.set_elastic_demand(None)
    assert demand.get_elastic_demand() is None


def test_set_elastic_demand_raises_when_reserve_price_is_set():
    reserve_price = ReservePrice(value=10.0, unit="NOK/MWh")
    demand = Demand(node="node", reserve_price=reserve_price)
    elastic_demand = ElasticDemand(
        price_elasticity=Elasticity(),
        min_price=Price(value=2.0, unit="NOK/MWh"),
        normal_price=Price(value=5.0, unit="NOK/MWh"),
        max_price=Price(value=10.0, unit="NOK/MWh"),
    )
    with pytest.raises(ValueError, match="Cannot set elastic_demand when reserve_price is not None."):
        demand.set_elastic_demand(elastic_demand)


def test_set_elastic_demand_type_check():
    demand = Demand(node="node")
    with pytest.raises(TypeError):
        demand.set_elastic_demand("not_an_elastic_demand")


def test_replace_node_replaces_node_when_old_matches():
    demand = Demand(node="old_node")
    demand._replace_node("old_node", "new_node")
    assert demand.get_node() == "new_node"


def test_replace_node_raises_value_error_when_old_does_not_match():
    demand = Demand(node="existing_node")
    with pytest.raises(ValueError, match="not found in .* Expected existing node existing_node."):
        demand._replace_node("wrong_node", "new_node")


def test_get_simpler_components_returns_dict_with_flow():
    demand = Demand(node="node")

    result = demand._get_simpler_components("base")

    assert isinstance(result, dict)
    assert "base_Flow" in result

    flow = result["base_Flow"]
    assert isinstance(flow, Flow)


def test_create_flow_exogenous_no_reserve_price_no_elastic_demand():
    demand = Demand(node="node")

    flow = demand._create_flow()

    assert flow is not None
    assert isinstance(flow, Flow)
    assert flow.is_exogenous() is True
    assert flow.get_main_node() == "node"
    assert flow.get_max_capacity() == demand.get_capacity()
    assert flow.get_min_capacity() == demand.get_capacity()
    assert flow.get_volume() == demand.get_consumption()
    assert any(a.get_node() == "node" for a in flow.get_arrows())
    assert "reserve_price" not in flow.get_cost_terms()


def test_create_flow_with_reserve_price():
    reserve_price = ReservePrice(value=10.0, unit="NOK/MWh")
    demand = Demand(node="node", reserve_price=reserve_price)

    flow = demand._create_flow()

    assert flow.is_exogenous() is False
    assert flow.get_main_node() == "node"
    assert flow.get_max_capacity() == demand.get_capacity()
    assert flow.get_min_capacity() is None
    assert "reserve_price" in flow.get_cost_terms()
    assert flow.get_cost_terms()["reserve_price"] == reserve_price


def test_create_flow_with_elastic_demand():
    elastic_demand = ElasticDemand(
        price_elasticity=Elasticity(),
        min_price=Price(value=2.0, unit="NOK/MWh"),
        normal_price=Price(value=5.0, unit="NOK/MWh"),
        max_price=Price(value=10.0, unit="NOK/MWh"),
    )
    demand = Demand(node="node", elastic_demand=elastic_demand)

    flow = demand._create_flow()

    assert flow.is_exogenous() is False
    assert flow.get_main_node() == "node"
    assert flow.get_max_capacity() == demand.get_capacity()
    assert flow.get_min_capacity() is None
    assert "reserve_price" in flow.get_cost_terms()
    # The reserve_price should be constructed from elastic_demand.get_max_price()
    rp = flow.get_cost_terms()["reserve_price"]
    assert isinstance(rp, ReservePrice)
    assert rp.get_level() == elastic_demand.get_max_price().get_level()
    assert rp.get_profile() == elastic_demand.get_max_price().get_profile()
