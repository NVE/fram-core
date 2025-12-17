from framcore.attributes import Price
from framcore.components import Node


def test_init_minimal_args():
    node = Node(commodity="electricity")

    assert node.get_commodity() == "electricity"
    assert node.is_exogenous() is False
    assert isinstance(node.get_price(), Price)
    assert node.get_storage() is None


def test_init_all_args():
    price = Price()
    node = Node(commodity="gas", is_exogenous=True, price=price)

    assert node.get_commodity() == "gas"
    assert node.is_exogenous() is True
    assert node.get_price() is price
    assert node.get_storage() is None
