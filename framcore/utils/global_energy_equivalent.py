from framcore.components import Component, HydroModule
from framcore.curves import Curve
from framcore.expressions import Expr
from framcore.metadata import LevelExprMeta
from framcore.timevectors import ConstantTimeVector, TimeVector


def get_hydro_downstream_energy_equivalent(
    data: dict[str, Component | TimeVector | Curve | Expr],
    module_name: str,
    power_node: str | None = None,
) -> Expr:
    """
    Get the expression for the sum downstream energy equivalent for a hydro module.

    - If power node is given, only count downstream energy equivalents that are connected to the power node.
    - Energy equivalents are collected from hydro generators downstream, and the main topology follows the release_to attribute.
    - Transport pumps are included in the downstream topology, but counted as negative energy equivalents.

    Args:
        data (dict[str, Component | TimeVector | Curve | Expr]): The dict containing the components.
        module_name (str): The name of the hydro module to start from.
        power_node (str): Optional power node to filter energy equivalents.

    """
    if data[module_name].get_pump() and data[module_name].get_pump().get_from_module() == module_name:  # transport pump
        pump_power_node = data[module_name].get_pump().get_power_node()
        pump_to = data[module_name].get_pump().get_to_module()
        energy_equivalent = get_hydro_downstream_energy_equivalent(data, pump_to, power_node)  # continue downstream of pump_to module
        if power_node in (pump_power_node, None):
            return energy_equivalent - data[module_name].get_pump().get_energy_equivalent().get_level()  # pumps has negative energy equivalents
        return energy_equivalent

    energy_equivalent = 0
    if data[module_name].get_generator():  # hydro generator
        module_power_node = data[module_name].get_generator().get_power_node()
        if power_node in (module_power_node, None):
            energy_equivalent += data[module_name].get_generator().get_energy_equivalent().get_level()
    if data[module_name].get_release_to():  # continue from release_to module
        release_to = data[module_name].get_release_to()
        energy_equivalent += get_hydro_downstream_energy_equivalent(data, release_to, power_node)
    return energy_equivalent


def set_global_energy_equivalent(data: dict[str, Component | TimeVector | Curve | Expr], metakey_energy_eq_downstream: str) -> None:
    """
    Loop through data dict and set the downstream energy equivalent for all HydroModules.

    Send a warning event if a HydroModule has no downstream energy equivalents.

    Args:
        data (dict[str, Component | TimeVector | Curve | Expr]): The dict containing the components.
        metakey_energy_eq_downstream (str): The meta key to use for storing the downstream energy equivalent.

    """
    for module_name, module in data.items():
        if isinstance(module, HydroModule) and module.get_reservoir():
            energy_equivalent = get_hydro_downstream_energy_equivalent(data, module_name)
            if energy_equivalent == 0:
                message = f"HydroModule {module_name} has no downstream energy equivalents."
                module.send_warning_event(message)
                energy_equivalent = ConstantTimeVector(scalar=0.0, unit="kWh/m3", is_max_level=False)
            module.add_meta(metakey_energy_eq_downstream, LevelExprMeta(energy_equivalent))
