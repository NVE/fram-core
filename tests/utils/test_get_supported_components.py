from unittest.mock import Mock

import pytest

from framcore.components import Component
from framcore.utils import get_supported_components as gsc


class SupportedComponent(Component):
    pass


class UnsupportedComponent(Component):
    pass


class FobiddenComponent(Component):
    pass


def test_gsc_if_candidates_contain_forbidden_component_raise_value_error():
    components = {"comp1": Mock(FobiddenComponent)}
    forbidden = (FobiddenComponent,)

    with pytest.raises(ValueError, match="has forbidden component"):
        gsc(components=components, supported_types=(), forbidden_types=forbidden)


def test_gsc_when_component_in_supported_types_it_is_in_output():
    component = Mock(SupportedComponent)
    components = {"comp1": component}
    supported = (SupportedComponent,)

    output = gsc(components=components, supported_types=supported, forbidden_types=())

    assert "comp1" in output
    assert output["comp1"] == component


def test_gsc_when_component_not_in_supported_types_simplify_until_supported():
    supported_component = Mock(SupportedComponent)
    unsupported_component = Mock(UnsupportedComponent)
    unsupported_component.get_simpler_components.return_value = {"supported_comp": supported_component}

    components = {"comp1": unsupported_component}
    supported = (SupportedComponent,)

    output = gsc(components=components, supported_types=supported, forbidden_types=())

    assert "supported_comp" in output
    assert output["supported_comp"] == supported_component


def test_gsc_if_simplified_component_is_forbidden_raise_value_error():
    forbidden_component = Mock(FobiddenComponent)
    unsupported_component = Mock(UnsupportedComponent)
    unsupported_component.get_simpler_components.return_value = {"forbidden_comp": forbidden_component}

    components = {"comp1": unsupported_component}
    supported = (SupportedComponent,)
    forbidden = (FobiddenComponent,)

    with pytest.raises(ValueError, match="has forbidden component"):
        gsc(components=components, supported_types=supported, forbidden_types=forbidden)


def test_gsc_multiple_levels_of_simplification_until_supported():
    mid_component = Mock(UnsupportedComponent)
    supported_component1 = Mock(SupportedComponent)
    mid_component.get_simpler_components.return_value = {"supported_comp_1": supported_component1}

    top_component_1 = Mock(UnsupportedComponent)
    supported_component2 = Mock(SupportedComponent)
    top_component_1.get_simpler_components.return_value = {"mid_comp": mid_component, "supported_comp_2": supported_component2}

    top_component_2 = Mock(UnsupportedComponent)
    supported_component_3 = Mock(SupportedComponent)
    top_component_2.get_simpler_components.return_value = {"supported_comp_3": supported_component_3}

    components = {"comp1": top_component_1, "comp2": top_component_2}
    supported = (SupportedComponent,)

    output = gsc(components=components, supported_types=supported, forbidden_types=())

    assert len(output) == 3
    assert "supported_comp_1" in output
    assert output["supported_comp_1"] == supported_component1
    assert "supported_comp_2" in output
    assert output["supported_comp_2"] == supported_component2
    assert "supported_comp_3" in output
    assert output["supported_comp_3"] == supported_component_3
    assert "mid_comp" not in output
    assert "comp1" not in output
    assert "comp2" not in output


def test_gsc_if_no_supported_component_found_raise_value_error():
    component = Mock(UnsupportedComponent)
    component.get_simpler_components.return_value = {}

    components = {"comp1": component}
    supported = (SupportedComponent,)

    with pytest.raises(ValueError, match="No component in the hierarchy was supported."):
        gsc(components=components, supported_types=supported, forbidden_types=())
