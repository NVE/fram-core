from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from framcore import Base
from framcore.curves import Curve, LoadedCurve
from framcore.fingerprints import Fingerprint, FingerprintRef
from framcore.timevectors import ConstantTimeVector, TimeVector

if TYPE_CHECKING:
    from framcore.loaders import Loader


# TODO: Add Expr.add_many to support faster aggregation expressions.
class Expr(Base):
    """
    Mathematical expression with TimeVectors and Curves to represent Levels and Profiles in LevelProfiles.

    The simplest Expr is a single TimeVector, while a more complicated expression could be a weighted average of several TimeVectors or Expressions.
    Expr can also have string references to Expr, TimeVector or Curve in a database (often Model).

    Expr are classified as Stock, Flow or None of them. See https://en.wikipedia.org/wiki/Stock_and_flow. In FRAM we only support Flow data as a rate of change.
    So, for example, a production timeseries has to be in MW, and not in MWh. Converting between the two versions of Flow would add another
    level of complexity both in Expr and in TimeVector operations.

    Expr are also classified as Level, Profile or none of them. This classification, together with Stock or Flow,
    is used to check if the built Expr are legal operations.
    - Expr that are Level can contain its connected Profile Expr. This is used in the queries to evaluate Levels according to their ReferencePeriod, and
        convert between Level formats (max level or average level, see LevelProfile for more details).

    Calculations using Expr are evaluated lazily, reducing unnecessary numerical operations during data manipulation.
    Computations involving values and units occur only when the Expr is queried.

    We only support calculations using +, -, *, and / in Expr, and we have no plans to change this.
    Expanding beyond these would turn Expr into a complex programming language rather than keeping it as a simple
    and efficient system for common time-series calculations. More advanced operations are still possible through eager evaluation, so this is not a limitation.
    It simply distributes responsibilities across system components in a way that is practical from a maintenance perspective.

    We use SymPy to support unit conversions. Already computed unit conversion factors are cached to minimize redundant calculations.

    At the moment we support these queries for Expr (see Aggregators for more about how they are used):
    - get_level_value(expr, db, unit, data_dim, scen_dim, is_max)
        - Supports all expressions. Will evaluate level Exprs at data_dim (with reference period of scen_dim),
            and profile Exprs as an average over scen_dim (both as constants).
        - Has optimized fastpath methods for sums, products and aggregations. The rest uses a fallback method with SymPy.
    - get_profile_vector(expr, db, data_dim, scen_dim, is_zero_one, is_float32)
        - Supports expr = sum(weight[i] * profile[i]) where weight[i] is a unitless constant Expr with value >= 0, and profile[i] is a unitless profile Expr.

    """

    def __init__(
        self,
        src: str | Curve | TimeVector | None = None,
        is_stock: bool = False,
        is_flow: bool = False,
        is_profile: bool = False,
        is_level: bool = False,
        profile: Expr | None = None,
        operations: tuple[str, list[Expr]] | None = None,
    ) -> None:
        """
        Create new (immutable) Expression.

        Args:
            src (str | Curve | TimeVector | None, optional): Source of the values to be used in the Expression. Either a Curve or TimeVector object,
              or a reference to one of them. Defaults to None.
            is_stock (bool, optional): Flag to signify if the Expr represents a stock type variable. Defaults to False.
            is_flow (bool, optional): Flag to signify if the Expr represents a flow type variable. Defaults to False.
            is_profile (bool, optional): Flag to signify if the Expr represents a profile. Defaults to False.
            is_level (bool, optional): Flag to signify if the Expr represents a level. Defaults to False.
            profile (Expr | None, optional): Expr that are Level can contain its connected Profile Expr. This is used in the queries to evaluate
                Levels according to their ReferencePeriod, and convert between Level formats (max level or average level, see LevelProfile for more details).
            operations (tuple[str, list[Expr]] | None, optional): Operations to apply to the expression. Defaults to None.

        """
        if is_level and is_profile:
            message = "Expr cannot be both level and a profile. Set either is_level or is_profile True or both False."
            raise ValueError(message)

        if is_flow and is_stock:
            message = "Expr cannot be both flow and stock. Set either is_flow or is_stock True or both False."
            raise ValueError(message)

        if is_profile and (is_flow or is_stock):
            message = "Expr cannot be both a profile and a flow/stock. Profiles must be coefficients."
            raise ValueError(message)

        self._src: str | Curve | TimeVector | None = src
        self._is_stock = is_stock
        self._is_flow = is_flow
        self._is_profile = is_profile
        self._is_level = is_level
        self._profile = profile

        # have to come after setting fields
        # because fields are used to create
        # error messages e.g. in __repr__

        self._check_type(src, (str, Curve, TimeVector, type(None)))
        self._check_type(is_stock, (bool, type(None)))
        self._check_type(is_flow, (bool, type(None)))
        self._check_type(is_level, (bool, type(None)))
        self._check_type(is_profile, (bool, type(None)))
        self._check_type(profile, (Expr, type(None)))

        self._check_operations(operations)
        if operations is None:
            operations = "", []
        self._operations: tuple[str, list[Expr]] = operations

    def _check_operations(self, operations: tuple[str, list[Expr]] | None, expect_ops: bool = False) -> None:
        if operations is None:
            return
        self._check_type(operations, tuple)
        if len(operations) != 2:  # noqa: PLR2004
            message = f"Expected len(operations) == 2. Got: {operations}"
            raise ValueError(message)
        ops, args = operations
        self._check_type(ops, str)
        self._check_type(args, list)
        if ops == "":
            if expect_ops:
                message = f"Expected ops, but got {operations}"
                raise ValueError(message)
            if len(args) > 0:
                message = f"Expected ops to have length. Got {operations}"
                raise ValueError(message)
            return
        if len(ops) != len(args) - 1:
            message = f"Expected len(ops) == len(args) - 1. Got {operations}"
            raise ValueError(message)
        for op in ops:
            if op not in "+-/*":
                message = f"Expected all op in ops in +-*/. Got {operations}"
                raise ValueError(message)
        for ex in args:
            self._check_type(ex, Expr)

    def get_fingerprint(self) -> Fingerprint:
        """Return fingerprint."""
        fingerprint = Fingerprint(self)
        fingerprint.add("is_stock", self._is_stock)
        fingerprint.add("is_flow", self._is_flow)
        fingerprint.add("is_profile", self._is_profile)
        fingerprint.add("is_level", self._is_level)
        fingerprint.add("profile", self._profile)
        if self._src:
            fingerprint.add("src", self._src.get_fingerprint() if isinstance(self._src, TimeVector) else FingerprintRef(self._src))
        fingerprint.add("operations", self._operations)
        return fingerprint

    def is_leaf(self) -> bool:
        """Return True if self is not an operation expression."""
        return self._src is not None

    def get_src(self) -> str | Curve | TimeVector | None:
        """Return str, Curve or TimeVector (either reference to Curve/TimeVector or Curve/TimeVector itself) or None if self is an operation expression."""
        return self._src

    def get_operations(self, expect_ops: bool, copy_list: bool) -> tuple[str, list[Expr]]:
        """Return ops, args. Users of this (low level) API must supply expect_ops and copy_list args."""
        self._check_type(copy_list, bool)
        self._verify_operations(expect_ops)
        if copy_list:
            ops, args = self._operations
            return ops, copy(args)
        return self._operations

    def _verify_operations(self, expect_ops: bool = False) -> None:
        self._check_operations(self._operations, expect_ops)
        ops = self._operations[0]

        if not ops:
            return

        has_add = "+" in ops
        has_sub = "-" in ops
        has_mul = "*" in ops
        has_div = "/" in ops

        if (has_add or has_sub) and (has_mul or has_div):
            message = f"Found +- in same operation level as */ in operations {self._operations} "
            raise ValueError(message)

        if has_div:
            seen_div = False
            for op in ops:
                if op == "/":
                    seen_div = True
                    continue
                if seen_div and op != "/":
                    message = f"Found +-* after / in operations {self._operations}"
                    raise ValueError(message)

    def is_flow(self) -> bool:
        """Return True if flow. Cannot be stock and flow."""
        return self._is_flow

    def is_stock(self) -> bool:
        """Return True if stock. Cannot be stock and flow."""
        return self._is_stock

    def is_level(self) -> bool:
        """Return True if level. Cannot be level and profile."""
        return self._is_level

    def is_profile(self) -> bool:
        """Return True if profile. Cannot be level and profile."""
        return self._is_profile

    def get_profile(self) -> Expr | None:
        """Return Expr representing profile. Implies self.is_level() is True."""
        return self._profile

    def set_profile(self, profile: Expr | None) -> None:
        """Set the profile of the Expr. Implies self.is_level() is True."""
        if not self.is_level():
            raise ValueError("Cannot set profile on Expr that is not a level.")
        self._profile = profile

    def _analyze_op(self, op: str, other: Expr) -> tuple[bool, bool, bool, bool, Expr | None]:
        flow = (True, False)
        stock = (False, True)
        level = (True, False)
        profile = (False, True)
        none = (False, False)

        supported_cases = {
            # all op supported for none
            ("+", none, none, none, none): (none, none, None),
            ("-", none, none, none, none): (none, none, None),
            ("*", none, none, none, none): (none, none, None),
            ("/", none, none, none, none): (none, none, None),
            # + flow level
            ("+", flow, level, flow, level): (flow, level, None),
            # * flow level
            ("*", flow, level, none, none): (flow, level, self.get_profile()),
            ("*", none, none, flow, level): (flow, level, other.get_profile()),
            # / flow level
            ("/", flow, level, none, none): (flow, level, self.get_profile()),
            ("/", flow, level, flow, level): (none, none, None),
            # + stock level
            ("+", stock, level, stock, level): (stock, level, None),
            # * stock level
            ("*", stock, level, none, level): (stock, level, None),
            ("*", none, level, stock, level): (stock, level, None),
            ("*", stock, level, none, none): (stock, level, self.get_profile()),
            ("*", none, none, stock, level): (stock, level, other.get_profile()),
            # / stock level
            ("/", stock, level, none, level): (stock, level, None),
            ("/", stock, level, none, none): (stock, level, self.get_profile()),
            ("/", stock, level, stock, level): (none, none, None),
            # level * level ok if one is flow (i.e. price * volume) or none (co2_eff / eff)
            ("*", flow, level, none, level): (flow, level, None),
            ("*", none, level, flow, level): (flow, level, None),
            ("/", flow, level, none, level): (flow, level, None),
            ("/", none, level, none, level): (none, level, None),
            ("*", none, level, none, level): (none, level, None),
            # profile
            ("+", none, profile, none, profile): (none, profile, None),
            ("-", none, profile, none, profile): (none, profile, None),
            ("/", none, profile, none, none): (none, profile, None),
            ("*", none, profile, none, none): (none, profile, None),
            ("*", none, none, none, profile): (none, profile, None),
            ("/", none, none, none, profile): (none, profile, None),
            # level
            ("+", none, level, none, level): (none, level, None),
            ("-", none, level, none, level): (none, level, None),
            ("/", none, level, none, none): (none, level, self.get_profile()),
            ("*", none, level, none, none): (none, level, self.get_profile()),
            ("*", none, none, none, level): (none, level, other.get_profile()),
            ("/", none, none, none, level): (none, level, other.get_profile()),
        }

        case = (
            op,
            (self.is_flow(), self.is_stock()),
            (self.is_level(), self.is_profile()),
            (other.is_flow(), other.is_stock()),
            (other.is_level(), other.is_profile()),
        )

        if case not in supported_cases:
            printable_case = {
                "op": case[0],
                "self_is_flow": case[1][0],
                "self_is_stock": case[1][1],
                "self_is_level": case[2][0],
                "self_is_profile": case[2][1],
                "other_is_flow": case[3][0],
                "other_is_stock": case[3][1],
                "other_is_level": case[4][0],
                "other_is_profile": case[4][1],
            }
            message = f"Unsupported case:\n{printable_case}\nexpression:\n{self} {op} {other}."
            raise ValueError(message)

        ((is_flow, is_stock), (is_level, is_profile), profile) = supported_cases[case]

        return is_stock, is_flow, is_level, is_profile, profile

    @staticmethod
    def _is_number(src: str) -> bool:
        try:
            float(src)
            return True
        except ValueError:
            return False

    def _create_op_expr(  # noqa: C901
        self,
        op: str,
        other: Expr | int | float,
        is_rhs: bool,
    ) -> Expr:
        if isinstance(other, Expr):
            is_stock, is_flow, is_level, is_profile, profile = self._analyze_op(op, other)

            x, y = (other, self) if is_rhs else (self, other)

            xisconst = isinstance(x.get_src(), ConstantTimeVector)
            yisconst = isinstance(y.get_src(), ConstantTimeVector)
            if xisconst and yisconst:
                xtv = x.get_src()
                ytv = y.get_src()
                is_combinable_tv = (
                    xtv.get_unit() == ytv.get_unit()
                    and xtv.is_max_level() == ytv.is_max_level()
                    and xtv.is_zero_one_profile() == ytv.is_zero_one_profile()
                    and xtv.get_reference_period() == ytv.get_reference_period()
                )
                if is_combinable_tv:
                    is_combinable_expr = (
                        x.is_level() == y.is_level()
                        and x.is_profile() == y.is_profile()
                        and x.is_flow() == y.is_flow()
                        and x.is_stock() == y.is_stock()
                        and x.get_profile() == y.get_profile()
                    )
                    if is_combinable_expr:
                        xscalar = xtv.get_vector(is_float32=True)[0]
                        yscalar = ytv.get_vector(is_float32=True)[0]
                        if op == "+":
                            scalar = xscalar + yscalar
                        elif op == "-":
                            scalar = xscalar - yscalar
                        elif op == "*":
                            scalar = xscalar * yscalar
                        elif op == "/":
                            scalar = xscalar / yscalar
                        return Expr(
                            src=ConstantTimeVector(
                                scalar=scalar,
                                unit=xtv.get_unit(),
                                is_max_level=xtv.is_max_level(),
                                is_zero_one_profile=xtv.is_zero_one_profile(),
                                reference_period=xtv.get_reference_period(),
                            ),
                            is_stock=x.is_stock(),
                            is_flow=x.is_flow(),
                            is_profile=x.is_profile(),
                            is_level=x.is_level(),
                            profile=x.get_profile(),
                            operations=None,
                        )

            ops, args = x.get_operations(expect_ops=False, copy_list=True)

            if not ops:
                ops = op
                args = [x, y]
            else:
                last_op = ops[-1]
                if last_op == op or (op in "+-" and last_op in "+-") or (last_op == "*" and op == "/"):
                    ops = f"{ops}{op}"
                    args.append(y)
                else:
                    ops = op
                    args = [x, y]

            return Expr(
                src=None,
                is_flow=is_flow,
                is_stock=is_stock,
                is_level=is_level,
                is_profile=is_profile,
                profile=profile,
                operations=(ops, args),
            )

        if self._is_number(other):
            if op in "*/":
                other_expr = Expr(src=ConstantTimeVector(float(other), is_max_level=False))
                return self._create_op_expr(op=op, other=other_expr, is_rhs=is_rhs)

            if op in "+" and other == 0:  # Comes from sum(expr_list). See sum() noqa
                return self  # TODO: Also accept 0 - Expr and -Expr?

            message = f"Only support multiplication and division with numbers, got {op} and {other}."
            raise ValueError(message)

        message = f"Only support Expr, int, float. Got unsupported type {type(other).__name__}."
        raise TypeError(message)

    def __add__(self, other: object) -> Expr:  # noqa: D105
        return self._create_op_expr("+", other, is_rhs=False)

    def __sub__(self, other: object) -> Expr:  # noqa: D105
        return self._create_op_expr("-", other, is_rhs=False)

    def __mul__(self, other: object) -> Expr:  # noqa: D105
        return self._create_op_expr("*", other, is_rhs=False)

    def __truediv__(self, other: object) -> Expr:  # noqa: D105
        return self._create_op_expr("/", other, is_rhs=False)

    def __radd__(self, other: object) -> Expr:  # noqa: D105
        return self._create_op_expr("+", other, is_rhs=True)

    def __rsub__(self, other: object) -> Expr:  # noqa: D105
        return self._create_op_expr("-", other, is_rhs=True)

    def __rmul__(self, other: object) -> Expr:  # noqa: D105
        return self._create_op_expr("*", other, is_rhs=True)

    def __rtruediv__(self, other: object) -> Expr:  # noqa: D105
        return self._create_op_expr("/", other, is_rhs=True)

    def __repr__(self) -> str:
        """Represent Expr as str."""
        if self._src is not None:
            return f"Expr({self._src})"
        ops, args = self.get_operations(expect_ops=True, copy_list=False)
        out = f"{args[0]}"
        for op, arg in zip(ops, args[1:], strict=True):
            out = f"{out} {op} {arg}"
        return f"Expr({out})"

    def __eq__(self, other) -> bool:  # noqa: ANN001
        """Check if self and other are equal."""
        if not isinstance(other, type(self)):
            return False
        return (
            self._is_flow == other._is_flow
            and self._is_level == other._is_level
            and self._src == other._src
            and self._is_stock == other._is_stock
            and self._is_profile == other._is_profile
            and self._profile == other._profile
            and self._operations[0] == other._operations[0]
            and len(self._operations[1]) == len(other._operations[1])
            and all([self._operations[1][i] == other._operations[1][i] for i in range(len(self._operations[1]))])  # noqa: SLF001
        )

    def __hash__(self) -> int:
        """Compute hash value.."""
        return hash(
            (
                self._is_flow,
                self._is_stock,
                self._is_level,
                self._is_profile,
                self._src,
                self._profile,
                self._operations[0],
                tuple(self._operations[1]),
            ),
        )

    def add_loaders(self, loaders: set[Loader]) -> None:
        """Add all loaders stored in TimeVector or Curve within Expr to loaders."""
        if self.is_leaf():
            src = self.get_src()
            if isinstance(src, TimeVector | LoadedCurve):
                loader = src.get_loader()
                if loader is not None:
                    loaders.add(loader)
            return
        __, args = self.get_operations(expect_ops=True, copy_list=False)
        for arg in args:
            arg.add_loaders(loaders)


# Proposed new way of creating Expr in classes.
def ensure_expr(
    value: Expr | str | Curve | TimeVector | None,  # technically anything that can be converted to float. Typehint for this?
    is_flow: bool = False,
    is_stock: bool = False,
    is_level: bool = False,
    is_profile: bool = False,
    profile: Expr | None = None,
) -> Expr | None:
    """
    Ensure that the value is an expression of the expected type or create one if possible.

    Args:
        value (Expr | str | None): The value to check.
        is_flow (str): If the Expr is a flow. Cannot be True if is_stock is True.
        is_stock (str): If the Expr is a stock. Cannot be True if is_flow is True.
        is_level (bool): Wether the Expr represents a level. Cannot be True if is_profile is True.
        is_profile (bool): Wether the Expr represents a profile. Cannot be True if is_level is True.
        profile (Expr | None): If the Expr is a level, this should be its profile.

    Returns:
        value (Expr | str): The value as an expression of the expected type or None.

    """
    if not isinstance(value, (str, Expr, Curve, TimeVector)) and value is not None:
        msg = f"Expected value to be of type Expr, str, Curve, TimeVector or None. Got {type(value).__name__}."
        raise TypeError(msg)

    if value is None:
        return None

    if isinstance(value, Expr):
        # Check wether given Expr matches expected flow, stock, profile and level status.
        if value.is_flow() != is_flow or value.is_stock() != is_stock or value.is_level() != is_level or value.is_profile() != is_profile:
            message = (
                "Given Expr has a mismatch between expected and actual flow/stock or level/profile status:\nExpected: "
                f"is_flow - {is_flow}, is_stock - {is_stock}, is_level - {is_level}, is_profile - {is_profile}\n"
                f"Actual: is_flow - {value.is_flow()}, is_stock - {value.is_stock()}, "
                f"is_level - {value.is_level()}, is_profile - {value.is_profile()}"
            )
            raise ValueError(message)
        return value

    return Expr(
        src=value,
        is_flow=is_flow,
        is_stock=is_stock,
        is_level=is_level,
        is_profile=is_profile,
        profile=profile,
    )


def get_profile_exprs_from_leaf_levels(expr: Expr) -> list[Expr]:
    """
    Get all profile expressions from leaf-level Expr objects that are marked as levels.

    Args:
        expr (Expr): The starting Expr object.

    Returns:
        list[Expr]: A list of profile expressions from leaf-level Expr objects.

    """
    profile_exprs = []

    def _traverse(expr: Expr) -> None:
        if expr.is_leaf():
            if expr.is_level() and expr.get_profile() is not None:
                profile_exprs.append(expr.get_profile())
            return

        # Recursively traverse the arguments of the expression
        _, args = expr.get_operations(expect_ops=False, copy_list=False)
        for arg in args:
            _traverse(arg)

    _traverse(expr)
    return profile_exprs


def get_leaf_profiles(expr: Expr) -> list[Expr]:
    """
    Get all leaf profile expressions from an Expr object.

    Args:
        expr (Expr): The starting Expr object.

    Returns:
        list[Expr]: A list of leaf profile expressions.

    """
    leaf_profiles = []

    def _traverse(expr: Expr) -> None:
        if expr.is_leaf():
            if expr.is_profile():
                leaf_profiles.append(expr)
            return

        # Recursively traverse the arguments of the expression
        _, args = expr.get_operations(expect_ops=False, copy_list=False)
        for arg in args:
            _traverse(arg)

    _traverse(expr)
    return leaf_profiles
