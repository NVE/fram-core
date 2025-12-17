from framcore import Base
from framcore.attributes import AvgFlowVolume, Conversion, FlowVolume
from framcore.expressions import Expr, ensure_expr
from framcore.fingerprints import Fingerprint
from framcore.timevectors import TimeVector


class HydroPump(Base):
    """
    Represent a pump associated with a HydroModule.

    The HydroPump can consume power from a power Node to move water upstream between two HydroModules. It has a max power capacity, and mean energy
    equivalent and water capacity. It can also describe the relationship between head and flow (Q), with min and max head and flow.

    Results for water and power consumption are stored as AvgFlowVolume attributes.

    """

    def __init__(
        self,
        power_node: str,
        from_module: str,
        to_module: str,
        water_capacity: FlowVolume,
        energy_equivalent: Conversion,
        power_capacity: FlowVolume | None = None,
        head_min: Expr | str | TimeVector | None = None,
        head_max: Expr | str | TimeVector | None = None,
        q_min: Expr | str | TimeVector | None = None,
        q_max: Expr | str | TimeVector | None = None,
    ) -> None:
        """
        Initialize a HydroPump object parameters.

        Args:
            power_node (str): Node to take power from when operating.
            from_module (str): Source HydroModule to move water from.
            to_module (str): Destination HydroModule to move water to.
            water_capacity (FlowVolume): Max pumped water volume given the mean energy equivalent and power capacity.
            energy_equivalent (Conversion): Mean conversion factor between power consumed and volume of water moved.
            power_capacity (FlowVolume | None, optional): Max power consumed. Defaults to None.
            head_min (Expr | str | TimeVector | None, optional): Minimum elevation difference between upstream and downstream water level. Defaults to None.
            head_max (Expr | str | TimeVector | None, optional): Maximum elevation difference between upstream and downstream water level. Defaults to None.
            q_min (Expr | str | TimeVector | None, optional): Maximum water flow at head_min. Defaults to None.
            q_max (Expr | str | TimeVector | None, optional): Maximum water flow at head_max. Defaults to None.

        """
        super().__init__()
        self._check_type(power_node, str)
        self._check_modules(from_module, to_module)  # checks types and that they are not the same.
        self._check_type(water_capacity, FlowVolume)
        self._check_type(power_capacity, (FlowVolume, type(None)))
        self._check_type(energy_equivalent, Conversion)
        self._check_type(head_min, (Expr, str, TimeVector, type(None)))
        self._check_type(head_max, (Expr, str, TimeVector, type(None)))
        self._check_type(q_min, (Expr, str, TimeVector, type(None)))
        self._check_type(q_max, (Expr, str, TimeVector, type(None)))

        self._power_node = power_node
        self._from_module = from_module
        self._to_module = to_module
        self._water_capacity = water_capacity
        self._energy_eq = energy_equivalent
        self._power_capacity = power_capacity

        self._hmin = ensure_expr(head_min, is_level=True)
        self._hmax = ensure_expr(head_max, is_level=True)
        self._qmin = ensure_expr(q_min, is_flow=True, is_level=True)
        self._qmax = ensure_expr(q_max, is_flow=True, is_level=True)

        self._water_consumption = AvgFlowVolume()
        self._power_consumption = AvgFlowVolume()

    def get_water_capacity(self) -> FlowVolume:
        """Get the capacity of the pump unit."""
        return self._water_capacity

    def get_power_capacity(self) -> FlowVolume:
        """Get the capacity of the pump unit."""
        return self._power_capacity

    def get_power_node(self) -> str:
        """Get the power node of the pump unit."""
        return self._power_node

    def set_power_node(self, power_node: str) -> None:
        """Set the power node of the pump unit."""
        self._check_type(power_node, str)
        self._power_node = power_node

    def get_from_module(self) -> str:
        """Get the module from which the pump unit is pumping."""
        return self._from_module

    def get_to_module(self) -> str:
        """Get the module to which the pump unit is pumping."""
        return self._to_module

    # TODO: should be split in two? Keep in mind we check that the to and from modules are not the same. So if we split this user might run into issues if
    # trying to first set from_module to to_module then change to_module.
    def set_modules(self, from_module: str, to_module: str) -> None:
        """Set the modules for the pump unit."""
        self._check_modules(from_module, to_module)
        self._from_module = from_module
        self._to_module = to_module

    def get_water_consumption(self) -> FlowVolume:
        """Get the water consumption of the pump unit."""
        return self._water_consumption

    def get_power_consumption(self) -> FlowVolume:
        """Get the power consumption of the pump unit."""
        return self._power_consumption

    def _check_modules(self, from_module: str, to_module: str) -> None:
        self._check_type(from_module, str)
        self._check_type(to_module, str)
        if from_module == to_module:
            message = f"{self} cannot pump to and from the same module. Got {from_module} for both from_module and to_module."
            raise ValueError(message)

    def _check_base_module_name(self, base_name: str) -> None:
        if base_name not in (self._from_module, self._to_module):
            message = (
                f"Module {base_name} has not been coupled correctly to its pump {self}. Pump is coupled to modules {self._from_module} and {self._to_module}"
            )
            raise RuntimeError(message)

    # other parameters
    def get_energy_equivalent(self) -> Conversion:
        """Get the energy equivalent of hydro pump."""
        return self._energy_eq

    def set_energy_eq(self, energy_eq: Conversion) -> None:
        """Set the energy equivalent."""
        self._check_type(energy_eq, Conversion)
        self._energy_eq = energy_eq

    def get_head_min(self) -> Expr:
        """Get min fall height of hydro pump."""
        return self._head_min

    def set_head_min(self, head_min: Expr | str | None) -> None:
        """Set min fall height."""
        self._head_min = ensure_expr(head_min)

    def get_head_max(self) -> Expr:
        """Get max fall height of hydro pump."""
        return self._hmax

    def set_head_max(self, hmax: Expr | str | None) -> None:
        """Set max fall height."""
        self._hmax = ensure_expr(hmax)

    def get_q_min(self) -> Expr:
        """Get Q min of hydro pump."""
        return self._q_min

    def set_qmin(self, q_min: Expr | str | None) -> None:
        """Set Q min."""
        self._q_min = ensure_expr(q_min)

    def get_q_max(self) -> Expr:
        """Get Q max of hydro pump."""
        return self._q_max

    def set_qmax(self, q_max: Expr | str | None) -> None:
        """Set Q max."""
        self._q_max = ensure_expr(q_max)

    def _get_fingerprint(self) -> Fingerprint:
        return self.get_fingerprint_default(
            refs={
                "power_node": self._power_node,
                "from_module": self._from_module,
                "to_module": self._to_module,
            },
        )
