from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from framcore import Base
from framcore.expressions import (
    Expr,
    ensure_expr,
    get_leaf_profiles,
    get_level_value,
    get_profile_exprs_from_leaf_levels,
    get_profile_vector,
    get_timeindexes_from_expr,
    get_units_from_expr,
)
from framcore.expressions._get_constant_from_expr import _get_constant_from_expr
from framcore.querydbs import QueryDB
from framcore.timeindexes import FixedFrequencyTimeIndex, SinglePeriodTimeIndex, TimeIndex
from framcore.timevectors import ConstantTimeVector, ReferencePeriod, TimeVector

if TYPE_CHECKING:
    from framcore import Model
    from framcore.loaders import Loader


# TODO: Name all abstract classes Abstract[clsname]
class LevelProfile(Base, ABC):
    """
    Attributes representing timeseries data for Components. Mostly as Level * Profile, where both Level and Profile are Expr (expressions).

    Level and Profile represent two distinct dimensions of time. This is because we want to simulate future system states with historical weather patterns.
    Therefore, Level represents the system state at a given time (data_dim), while Profile represents the scenario dimension (scen_dim).
    A Level would for example represent the installed capacity of solar plants towards 2030,
    while the Profile would represent the historical variation between 1991-2020.

    Level and Profile can have two main formats: A maximum Level with a Profile that varies between 0-1,
    and an average Level with a Profile with a mean of 1 (the latter can have a ReferencePeriod).
    The max format is, for example, used for capacities, while the mean format can be used for prices and flows.
    The system needs to be able to convert between the two formats. This is especially important for aggregations
    (for example weighted averages) where all the TimeVectors need to be on the same format for a correct result.
    One simple example of conversion is pairing a max Level of 100 MW with a mean_one Profile [0, 1, 2].
    Asking for this on the max format will return the series 100*[0, 0.5, 1] MW, while on the avg format it will return 50*[0, 1, 2] MW.

    Queries to LevelProfile need to provide a database, the desired target TimeIndex for both dimensions, the target unit and the desired format.
    At the moment we support these queries for LevelProfile:
    - self.get_data_value(db, scen_dim, data_dim, unit, is_max_level)
    - self.get_scenario_vector(db, scen_dim, data_dim, unit, is_float32)

    In addition, we have the possibility to shift, scale, and change the intercept of the LevelProfiles.
    Then we get the full representation: Scale * (Level + Level_shift) * Profile + Intercept.
    - Level_shift adds a constant value to Level, has the same Profile as Level.
    - Scale multiplies (Level + Level_shift) by a constant value.
    - Intercept adds a constant value to LevelProfile, ignoring Level and Profile. **This is the only way of supporting a timeseries that crosses zero
        in our system. This functionality is under development and has not been properly tested.**

    LevelProfiles also have additional properties that describes their behaviour. These can be used for initialization, validation,
    and to simplify queries. The properties are:
    - is_stock: True if attribute is a stock variable. Level Expr should also have is_stock=True. See Expr for details.
    - is_flow: True if attribute is a flow variable. Level Expr should also have is_flow=True. See Expr for details.
    - is_not_negative: True if attribute is not allowed to have negative values. Level Expr should also have only non-negative values.
    - is_max_and_zero_one: Preferred format of Level and Profile. Used for initialization and queries.
    - is_ingoing: True if attribute is ingoing, False if outgoing, None if neither.
    - is_cost: True if attribute is objective function cost coefficient. Else None.
    - is_unitless: True if attribute is known to be unitless. False if known to have a unit that is not None. Else None.

    """

    # must be overwritten by subclass when otherwise
    # don't change the defaults
    _IS_ABSTRACT: bool = True
    _IS_STOCK: bool = False
    _IS_FLOW: bool = False
    _IS_NOT_NEGATIVE: bool = True
    _IS_MAX_AND_ZERO_ONE: bool = False

    # must be set by subclass when applicable
    _IS_INGOING: bool | None = None
    _IS_COST: bool | None = None
    _IS_UNITLESS: bool | None = None

    def __init__(
        self,
        level: Expr | TimeVector | str | None = None,
        profile: Expr | TimeVector | str | None = None,
        value: float | int | None = None,  # To support Price(value=20, unit="EUR/MWh")
        unit: str | None = None,
        level_shift: Expr | None = None,
        intercept: Expr | None = None,
        scale: Expr | None = None,
    ) -> None:
        """
        Initialize LevelProfile.

        See the LevelProfile class docstring for details. A complete LevelProfile is represented as:
        Scale * (Level + Level_shift) * Profile + Intercept. Normally only Level and Profile are used.

        Either give level and profile, or value and unit.

        Args:
            level (Expr | TimeVector | str | None, optional): Level Expr. Defaults to None.
            profile (Expr | TimeVector | str | None, optional): Profile Expr. Defaults to None.
            value (float | int | None, optional): A constant value to initialize Level. Defaults to None.
            unit (str | None, optional): Unit of the constant value to initialize Level. Defaults to None.
            level_shift (Expr | None, optional): Level_shift Expr. Defaults to None.
            intercept (Expr | None, optional): Intercept Expr. Defaults to None.
            scale (Expr | None, optional): Scale Expr. Defaults to None.

        """
        self._assert_invariants()

        self._check_type(value, (float, int, type(None)))
        self._check_type(unit, (str, type(None)))
        self._check_type(level, (Expr, TimeVector, str, type(None)))
        self._check_type(profile, (Expr, TimeVector, str, type(None)))
        self._check_type(level_shift, (Expr, type(None)))
        self._check_type(intercept, (Expr, type(None)))
        self._check_type(scale, (Expr, type(None)))
        level = self._ensure_level_expr(level, value, unit)
        profile = self._ensure_profile_expr(profile)
        self._ensure_compatible_level_profile_combo(level, profile)
        self._ensure_compatible_level_profile_combo(level_shift, profile)
        self._level: Expr | None = level
        self._profile: Expr | None = profile
        self._level_shift: Expr | None = level_shift
        self._intercept: Expr | None = intercept
        self._scale: Expr | None = scale
        # TODO: Validate that profiles are equal in level and level_shift.
        # TODO: Validate that level_shift, scale and intercept only consist of Exprs with ConstantTimeVectors
        # TODO: Validate that level_shift, level_scale and intercept have correct Expr properties

    def _assert_invariants(self) -> None:
        abstract = self._IS_ABSTRACT
        max_level_profile = self._IS_MAX_AND_ZERO_ONE
        stock = self._IS_STOCK
        flow = self._IS_FLOW
        unitless = self._IS_UNITLESS
        ingoing = self._IS_INGOING
        cost = self._IS_COST
        not_negative = self._IS_NOT_NEGATIVE

        assert not abstract, "Abstract types should only be used for type hints and checks."
        assert isinstance(max_level_profile, bool)
        assert isinstance(stock, bool)
        assert isinstance(flow, bool)
        assert isinstance(not_negative, bool)
        assert isinstance(ingoing, bool | type(None))
        assert isinstance(unitless, bool | type(None))
        assert isinstance(cost, bool | type(None))
        assert not (flow and stock)
        if flow or stock:
            assert not unitless, "flow and stock must have unit that is not None."
            assert not_negative, "flow and stock cannot have negative values."
        if ingoing is True:
            assert cost is None, "cost must be None when ingoing is True."
        if cost is True:
            assert ingoing is None, "ingoing must be None when cost is True."

        parent = super()
        if isinstance(parent, LevelProfile) and not parent._IS_ABSTRACT:  # noqa: SLF001
            self._assert_same_behaviour(parent)

    def add_loaders(self, loaders: set[Loader]) -> None:
        """Add all loaders stored in expressions to loaders."""
        from framcore.utils import add_loaders_if

        add_loaders_if(loaders, self.get_level())
        add_loaders_if(loaders, self.get_profile())

    def clear(self) -> None:
        """
        Set all internal fields to None.

        You may want to use this to get exogenous flow to use capacities instead of volume.
        """
        self._level = None
        self._profile = None
        self._level_shift = None
        self._intercept = None
        self._scale = None

    def is_stock(self) -> bool:
        """
        Return True if attribute is a stock variable.

        Return False if attribute is not a stock variable.
        """
        return self._IS_STOCK

    def is_flow(self) -> bool:
        """
        Return True if attribute is a flow variable.

        Return False if attribute is not a flow variable.
        """
        return self._IS_FLOW

    def is_not_negative(self) -> bool:
        """
        Return True if attribute is not allowed to have negative values.

        Return False if attribute can have both positive and negative values.
        """
        return self._IS_NOT_NEGATIVE

    def is_max_and_zero_one(self) -> bool:
        """
        When True level should be max (not average) and corresponding profile should be zero_one (not mean_one).

        When False level should be average (not max) and corresponding profile should be mean_one (not zero_one).
        """
        return self._IS_MAX_AND_ZERO_ONE

    def is_ingoing(self) -> bool | None:
        """
        Return True if attribute is ingoing.

        Return True if attribute is outgoing.

        Return None if not applicable.
        """
        return self._IS_INGOING

    def is_cost(self) -> bool | None:
        """
        Return True if attribute is objective function cost coefficient.

        Return False if attribute is objective function revenue coefficient.

        Return None if not applicable.
        """
        return self._IS_COST

    def is_unitless(self) -> bool | None:
        """
        Return True if attribute is known to be unitless.

        Return False if attribute is known to have a unit that is not None.

        Return None if not applicable.
        """
        return self._IS_UNITLESS

    def has_level(self) -> bool:
        """Return True if get_level will return value not None."""
        return (self._level is not None) or (self._level_shift is not None)

    def has_profile(self) -> bool:
        """Return True if get_profile will return value not None."""
        return self._profile is not None

    def has_intercept(self) -> bool:
        """Return True if get_intercept will return value not None."""
        return self._intercept is not None

    def copy_from(self, other: LevelProfile) -> None:
        """Copy fields from other."""
        self._check_type(other, LevelProfile)
        self._assert_same_behaviour(other)
        self._level = other._level
        self._profile = other._profile
        self._level_shift = other._level_shift
        self._intercept = other._intercept
        self._scale = other._scale

    def get_level(self) -> Expr | None:
        """Get level part of (level * profile + intercept)."""
        level = self._level

        if level is None:
            return None

        if level.is_leaf():
            level = Expr(
                src=level.get_src(),
                operations=level.get_operations(expect_ops=False, copy_list=True),
                is_stock=level.is_stock(),
                is_flow=level.is_flow(),
                is_level=True,
                is_profile=False,
                profile=self._profile,
            )

        if self._level_shift is not None:
            level += self._level_shift

        if self._scale is not None:
            level *= self._scale

        return level

    def set_level(self, level: Expr | TimeVector | str | None) -> None:
        """Set level part of (scale * (level + level_shift) * profile + intercept)."""
        self._check_type(level, (Expr, TimeVector, str, type(None)))
        level = self._ensure_level_expr(level)
        self._ensure_compatible_level_profile_combo(level, self._profile)
        self._level = level

    def get_profile(self) -> Expr | None:
        """Get profile part of (level * profile + intercept)."""
        return self._profile

    def set_profile(self, profile: Expr | TimeVector | str | None) -> None:
        """Set profile part of (scale * (level + level_shift) * profile + intercept)."""
        self._check_type(profile, (Expr, TimeVector, str, type(None)))
        profile = self._ensure_profile_expr(profile)
        self._ensure_compatible_level_profile_combo(self._level, profile)
        self._profile = profile

    def get_intercept(self) -> Expr | None:
        """Get intercept part of (level * profile + intercept)."""
        intercept = self._intercept
        if self._scale is not None:
            intercept *= self._scale
        return intercept

    def set_intercept(self, value: Expr | None) -> None:
        """Set intercept part of (level * profile + intercept)."""
        self._check_type(value, (Expr, type(None)))
        if value is not None:
            self._check_level_expr(value)
        self._intercept = value

    def get_level_unit_set(
        self,
        db: QueryDB | Model,
    ) -> set[TimeIndex]:
        """
        Return set with all units behind level expression.

        Useful for discovering valid unit input to get_level_value.
        """
        if not self.has_level():
            return set()
        return get_units_from_expr(db, self.get_level())

    def get_profile_timeindex_set(
        self,
        db: QueryDB | Model,
    ) -> set[TimeIndex]:
        """
        Return set with all TimeIndex behind profile expression.

        Can be used to run optimized queries, i.e. not asking for
        finer time resolutions than necessary.
        """
        if not self.has_profile():
            return set()
        return get_timeindexes_from_expr(db, self.get_profile())

    def get_scenario_vector(
        self,
        db: QueryDB | Model,
        scenario_horizon: FixedFrequencyTimeIndex,
        level_period: SinglePeriodTimeIndex,
        unit: str | None,
        is_float32: bool = True,
    ) -> NDArray:
        """
        Evaluate LevelProfile over the periods in scenario dimension, and at the level period of the data dimension.

        Underlying profiles are evalutated over the scenario dimension,
        and levels are evalutated to scalars over level_period in the data dimension.

        Args:
            db (QueryDB | Model): The database or model instance used to fetch the required data.
            scenario_horizon (FixedFrequencyTimeIndex): TimeIndex of the scenario dimension to evaluate profiles.
            level_period (SinglePeriodTimeIndex): TimeIndex of the data dimension to evaluate levels.
            unit (str | None): The unit to convert the resulting values into (e.g., MW, GWh). If None,
                the expression should be unitless.
            is_float32 (bool, optional): Whether to return the vector as a NumPy array with `float32`
                precision. Defaults to True.

        """
        return self._get_scenario_vector(db, scenario_horizon, level_period, unit, is_float32)

    def get_data_value(
        self,
        db: QueryDB | Model,
        scenario_horizon: FixedFrequencyTimeIndex,
        level_period: SinglePeriodTimeIndex,
        unit: str | None,
        is_max_level: bool | None = None,
    ) -> float:
        """
        Evaluate LevelProfile to a scalar at the level period of the data dimension, and as an average over the scenario horizon.

        Args:
            db (QueryDB | Model): The database or model instance used to fetch the required data.
            scenario_horizon (FixedFrequencyTimeIndex): TimeIndex of the scenario dimension to evaluate profiles.
            level_period (SinglePeriodTimeIndex): TimeIndex of the data dimension to evaluate levels.
            unit (str | None): The unit to convert the resulting values into (e.g., MW, GWh). If None,
                the expression should be unitless.
            is_max_level (bool | None, optional): Whether to evaluate the expression as a maximum level (with a zero_one profile)
                or as an average level (with a mean_one profile). If None, the default format of the attribute is used.

        """
        return self._get_data_value(db, scenario_horizon, level_period, unit, is_max_level)

    def shift_intercept(self, value: float, unit: str | None) -> None:
        """Modify the intercept part of (level * profile + intercept) of an attribute by adding a constant value."""
        expr = ensure_expr(
            ConstantTimeVector(self._ensure_float(value), unit=unit, is_max_level=False),
            is_level=True,
            is_profile=False,
            is_stock=self._IS_STOCK,
            is_flow=self._IS_FLOW,
            profile=None,
        )
        if self._intercept is None:
            self._intercept = expr
        else:
            self._intercept += expr

    def shift_level(
        self,
        value: float | int,
        unit: str | None = None,
        reference_period: ReferencePeriod | None = None,
        is_max_level: bool | None = None,
        use_profile: bool = True,  # TODO: Remove. Should always use profile. If has profile validate that it is equal to the profile of Level.
    ) -> None:
        """Modify the level_shift part of (scale * (level + level_shift) * profile + intercept) of an attribute by adding a constant value."""
        # TODO: Not allowed to shift if there is intercept?
        self._check_type(value, (float, int))
        self._check_type(unit, (str, type(None)))
        self._check_type(reference_period, (ReferencePeriod, type(None)))
        self._check_type(is_max_level, (bool, type(None)))
        self._check_type(use_profile, bool)

        if is_max_level is None:
            is_max_level = self._IS_MAX_AND_ZERO_ONE

        expr = ensure_expr(
            ConstantTimeVector(
                self._ensure_float(value),
                unit=unit,
                is_max_level=is_max_level,
                reference_period=reference_period,
            ),
            is_level=True,
            is_profile=False,
            is_stock=self._IS_STOCK,
            is_flow=self._IS_FLOW,
            profile=self._profile if use_profile else None,
        )
        if self._level_shift is None:
            self._level_shift = expr
        else:
            self._level_shift += expr

    def scale(self, value: float | int) -> None:
        """Modify the scale part of (scale * (level + level_shift) * profile + intercept) of an attribute by multiplying with a constant value."""
        # TODO: Not allowed to scale if there is intercept?
        expr = ensure_expr(
            ConstantTimeVector(self._ensure_float(value), unit=None, is_max_level=False),
            is_level=True,
            is_profile=False,
            profile=None,
        )
        if self._scale is None:
            self._scale = expr
        else:
            self._scale *= expr

    def _ensure_level_expr(
        self,
        level: Expr | str | TimeVector | None,
        value: float | int | None = None,
        unit: str | None = None,
        reference_period: ReferencePeriod | None = None,
    ) -> Expr | None:
        if value is not None:
            level = ConstantTimeVector(
                scalar=float(value),
                unit=unit,
                is_max_level=self._IS_MAX_AND_ZERO_ONE,
                is_zero_one_profile=None,
                reference_period=reference_period,
            )
        if level is None:
            return None

        if isinstance(level, Expr):
            self._check_level_expr(level)
            return level

        return Expr(
            src=level,
            is_flow=self._IS_FLOW,
            is_stock=self._IS_STOCK,
            is_level=True,
            is_profile=False,
            profile=None,
        )

    def _ensure_compatible_level_profile_combo(self, level: Expr | None, profile: Expr | None) -> None:
        """Check that all profiles in leaf levels (in level) also exist in profile."""
        if level is None or profile is None:
            return

        leaf_level_profiles = get_profile_exprs_from_leaf_levels(level)
        leaf_profile_profiles = get_leaf_profiles(profile)

        for p in leaf_level_profiles:
            if p not in leaf_profile_profiles:
                message = (
                    f"Incompatible level/profile combination because all profiles in leaf levels (in level) does not exist in profile. "
                    f"Profile expression {p} found in level {level} but not in profile."
                )
                raise ValueError(message)

    def _check_level_expr(self, expr: Expr) -> None:
        msg = f"{self} requires {expr} to be "
        if expr.is_stock() != self._IS_STOCK:
            raise ValueError(msg + f"is_stock={self._IS_STOCK}")
        if expr.is_flow() != self._IS_FLOW:
            raise ValueError(msg + f"is_flow={self._IS_STOCK}")
        if expr.is_level() is False:
            raise ValueError(msg + "is_level=True")
        if expr.is_profile() is True:
            raise ValueError(msg + "is_profile=False")

    def _check_profile_expr(self, expr: Expr) -> None:
        msg = f"{self} requires {expr} to be "
        if expr.is_stock() is True:
            raise ValueError(msg + "is_stock=False")
        if expr.is_flow() is True:
            raise ValueError(msg + "is_flow=False")
        if expr.is_level() is True:
            raise ValueError(msg + "is_level=False")
        if expr.is_profile() is False:
            raise ValueError(msg + "is_profile=True")

    def _ensure_profile_expr(
        self,
        value: Expr | str | TimeVector | None,
    ) -> Expr | None:
        if value is None:
            return None

        if isinstance(value, Expr):
            self._check_profile_expr(value)
            return value

        return Expr(
            src=value,
            is_flow=False,
            is_stock=False,
            is_level=False,
            is_profile=True,
            profile=None,
        )

    def _get_data_value(
        self,
        db: QueryDB,
        scenario_horizon: FixedFrequencyTimeIndex,
        level_period: SinglePeriodTimeIndex,
        unit: str | None,
        is_max_level: bool | None,
    ) -> float:
        # NB! don't type check db, as this is done in get_level_value and get_profile_vector
        self._check_type(scenario_horizon, FixedFrequencyTimeIndex)
        self._check_type(level_period, SinglePeriodTimeIndex)
        self._check_type(unit, (str, type(None)))
        self._check_type(is_max_level, (bool, type(None)))

        level_expr = self.get_level()

        if is_max_level is None:
            is_max_level = self._IS_MAX_AND_ZERO_ONE

        self._check_type(level_expr, (Expr, type(None)))
        if not isinstance(level_expr, Expr):
            raise ValueError("Attribute level Expr is None. Have you called Solver.solve yet?")

        level_value = get_level_value(
            expr=level_expr,
            db=db,
            scen_dim=scenario_horizon,
            data_dim=level_period,
            unit=unit,
            is_max=is_max_level,
        )

        intercept = None
        if self._intercept is not None:
            intercept = _get_constant_from_expr(
                self._intercept,
                db,
                unit=unit,
                data_dim=level_period,
                scen_dim=scenario_horizon,
                is_max=is_max_level,
            )

        if intercept is None:
            return level_value

        return level_value + intercept

    def _get_scenario_vector(
        self,
        db: QueryDB | Model,
        scenario_horizon: FixedFrequencyTimeIndex,
        level_period: SinglePeriodTimeIndex,
        unit: str | None,
        is_float32: bool = True,
    ) -> NDArray:
        """Return vector with values along the given scenario horizon using level over level_period."""
        # NB! don't type check db, as this is done in get_level_value and get_profile_vector
        self._check_type(scenario_horizon, FixedFrequencyTimeIndex)
        self._check_type(level_period, SinglePeriodTimeIndex)
        self._check_type(unit, (str, type(None)))
        self._check_type(is_float32, bool)

        level_expr = self.get_level()

        self._check_type(level_expr, (Expr, type(None)))
        if not isinstance(level_expr, Expr):
            raise ValueError("Attribute level Expr is None. Have you called Solver.solve yet?")

        level_value = get_level_value(
            expr=level_expr,
            db=db,
            scen_dim=scenario_horizon,
            data_dim=level_period,
            unit=unit,
            is_max=self._IS_MAX_AND_ZERO_ONE,
        )

        profile_expr = self.get_profile()

        if profile_expr is None:
            profile_vector = np.ones(
                scenario_horizon.get_num_periods(),
                dtype=np.float32 if is_float32 else np.float64,
            )
        else:
            profile_vector = get_profile_vector(
                expr=profile_expr,
                db=db,
                scen_dim=scenario_horizon,
                data_dim=level_period,
                is_zero_one=self._IS_MAX_AND_ZERO_ONE,
                is_float32=is_float32,
            )

        intercept = None
        if self._intercept is not None:
            intercept = _get_constant_from_expr(
                self._intercept,
                db,
                unit=unit,
                data_dim=level_period,
                scen_dim=scenario_horizon,
                is_max=self._IS_MAX_AND_ZERO_ONE,
            )

        if intercept is None:
            return level_value * profile_vector

        return level_value * profile_vector + intercept

    def _has_same_behaviour(self, other: LevelProfile) -> bool:
        return all(
            (
                self._IS_FLOW == other._IS_FLOW,
                self._IS_STOCK == other._IS_STOCK,
                self._IS_NOT_NEGATIVE == other._IS_NOT_NEGATIVE,
                self._IS_MAX_AND_ZERO_ONE == other._IS_MAX_AND_ZERO_ONE,
                self._IS_INGOING == other._IS_INGOING,
                self._IS_COST == other._IS_COST,
                self._IS_UNITLESS == other._IS_UNITLESS,
            ),
        )

    def _assert_same_behaviour(self, other: LevelProfile) -> None:
        if not self._has_same_behaviour(other):
            message = f"Not same behaviour for {self} and {other}"
            raise ValueError(message)

    def __eq__(self, other) -> bool:  # noqa: ANN001
        """Return True if other is equal to self."""
        if not isinstance(other, LevelProfile):
            return False
        if not self._has_same_behaviour(other):
            return False
        return all(
            (
                self._level == other._level,
                self._profile == other._profile,
                self._level_shift == other._level_shift,
                self._intercept == other._intercept,
                self._scale == other._scale,
            ),
        )

    def __hash__(self) -> int:
        """Compute hash of self."""
        return hash(
            (
                type(self).__name__,
                self._level,
                self._profile,
                self._level_shift,
                self._intercept,
                self._scale,
            ),
        )


# Abstract subclasses intended type hints and checks


class FlowVolume(LevelProfile):
    """
    Abstract class representing a flow volume attribute, indicating that the attribute is a flow variable.

    Subclass of LevelProfile. See LevelProfile for details.
    """

    _IS_FLOW = True


class Coefficient(LevelProfile):
    """
    Abstract class representing a coefficient attribute, used as a base class for various coefficient types.

    Subclass of LevelProfile. See LevelProfile for details.
    """

    pass


class ArrowCoefficient(Coefficient):
    """
    Abstract class representing an arrow coefficient attribute, used for efficiency, loss, and conversion coefficients.

    Subclass of Coefficient < LevelProfile. See LevelProfile for details.
    """

    pass


class ShadowPrice(Coefficient):
    """
    Abstract class representing a shadow price attribute, indicating that the attribute has a unit and might be negative.

    Subclass of Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_UNITLESS = False
    _IS_NOT_NEGATIVE = False


class ObjectiveCoefficient(Coefficient):
    """
    Abstract class representing an objective coefficient attribute, indicating cost or revenue coefficients in the objective function.

    Subclass of Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_UNITLESS = False
    _IS_NOT_NEGATIVE = False


# Concrete subclasses intended for final use


class Price(ShadowPrice):
    """
    Concrete class representing a price attribute, indicating the price of a commodity at a specific node.

    Subclass of ShadowPrice < Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False


class WaterValue(ShadowPrice):
    """
    Concrete class representing a water value attribute, indicating the value of water in the system.

    Subclass of ShadowPrice < Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False


class Cost(ObjectiveCoefficient):
    """
    Concrete class representing a cost attribute, indicating cost coefficients in the objective function.

    Subclass of ObjectiveCoefficient < Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False
    _IS_COST = True


class ReservePrice(ObjectiveCoefficient):
    """
    Concrete class representing a reserve price attribute, indicating revenue coefficients in the objective function.

    Subclass of ObjectiveCoefficient < Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False
    _IS_COST = False


class Elasticity(Coefficient):  # TODO: How do this work?
    """
    Concrete class representing an elasticity coefficient attribute, indicating a unitless coefficient.

    Subclass of Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False
    _IS_UNITLESS = True


class Proportion(Coefficient):
    """
    Concrete class representing a proportion coefficient attribute, indicating a unitless coefficient between 0 and 1.

    Subclass of Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False
    _IS_UNITLESS = True


class Hours(Coefficient):  # TODO: How do this work?
    """
    Concrete class representing an hours coefficient attribute, indicating a time-related coefficient.

    Subclass of Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False


class Efficiency(ArrowCoefficient):
    """
    Concrete class representing an efficiency coefficient attribute, indicating a unitless coefficient.

    Subclass of ArrowCoefficient < Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False
    _IS_UNITLESS = True


class Loss(ArrowCoefficient):  # TODO: Make a loss for storage that is percentage per time
    """
    Concrete class representing a loss coefficient attribute, indicating a unitless coefficient.

    Subclass of ArrowCoefficient < Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False
    _IS_UNITLESS = True


class Conversion(ArrowCoefficient):
    """
    Concrete class representing a conversion coefficient attribute, used for conversion factors in the model.

    Subclass of ArrowCoefficient < Coefficient < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False


class AvgFlowVolume(FlowVolume):
    """
    Concrete class representing an average flow volume attribute, indicating a flow variable with average values.

    Subclass of FlowVolume < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False


class MaxFlowVolume(FlowVolume):
    """
    Concrete class representing a maximum flow volume attribute, indicating a flow variable with maximum values.

    Subclass of FlowVolume < LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False
    _IS_MAX_AND_ZERO_ONE = True


class StockVolume(LevelProfile):
    """
    Concrete class representing a stock volume attribute, indicating a stock variable with maximum values.

    Subclass of LevelProfile. See LevelProfile for details.
    """

    _IS_ABSTRACT = False
    _IS_STOCK = True
    _IS_MAX_AND_ZERO_ONE = True
