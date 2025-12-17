from __future__ import annotations

from framcore.expressions import Expr, ensure_expr
from framcore.metadata.ExprMeta import ExprMeta  # NB! full import path needed for inheritance to work
from framcore.timevectors import TimeVector


class LevelExprMeta(ExprMeta):
    """
    LevelExprMeta represent an Expr. Subclass of ExprMeta.

    When used, all components must have a ExprMeta.
    """

    def __init__(self, value: Expr | TimeVector) -> None:
        """
        Create new LevelExprMeta with Expr value.

        Args:
            value (Expr | TimeVector): Accepts Expr with is_level=True or TimeVector with is_max_level=True/False.

        Raises:
            TypeError: If value is not Expr or TimeVector.
            ValueError: If value is non-level Expr or TimeVector.

        """
        self._check_type(value, (Expr, TimeVector))

        if isinstance(value, TimeVector) and value.is_max_level() is None:
            raise ValueError("Parameter 'value' (TimeVector) must be a level (is_max_level must be True or False).")

        self._value = ensure_expr(value, is_level=True)
