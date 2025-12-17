from collections import Counter
from typing import TYPE_CHECKING

from framcore import Base
from framcore.components import Component
from framcore.curves import Curve
from framcore.expressions import Expr
from framcore.timevectors import TimeVector

if TYPE_CHECKING:
    from framcore.aggregators import Aggregator


class ModelDict(dict):
    """Dict storing only values of type Component | Expr | TimeVector | Curve."""

    def __setitem__(self, key: str, value: Component | Expr | TimeVector | Curve) -> None:
        """Set item with type checking."""
        if not isinstance(key, str):
            message = f"Expected str for key {key}, got {type(key).__name__}"
            raise TypeError(message)
        if not isinstance(value, Component | Expr | TimeVector | Curve):
            message = f"Expected Component | Expr | TimeVector | Curve for key {key}, got {type(value).__name__}"
            raise TypeError(message)
        return super().__setitem__(key, value)


class Model(Base):
    """
    Model stores the representation of the energy system with Components, TimeVectors, Expression, and the Aggregators applied to the Model.

    - Components describe the main elements in the energy system. Can have additional Attributes.
    - TimeVector and Curve hold the time series data.
    - Expressions for data manipulation of TimeVectors and Curves. Can be queried.
    - Aggregators handle aggregation and disaggregation of Components. Aggregators are added to Model when used (Aggregator.aggregate(model)),
    and can be undone in LIFO order with disaggregate().

    Methods:
        get_data(): Get dict of Components, Expressions, TimeVectors and Curves stored in the Model. Can be modified.
        disaggregate(): Undo all aggregations applied to Model in LIFO order.
        get_content_counts(): Return number of objects stored in model organized into concepts and types.

    """

    def __init__(self) -> None:
        """Create a new model instance with empty data and no aggregators."""
        self._data = ModelDict()
        self._aggregators: list[Aggregator] = []

    def get_data(self) -> ModelDict:
        """Get dict of Components, Expressions, TimeVectors and Curves stored in the Model. Can be modified."""
        return self._data

    def disaggregate(self) -> None:
        """Undo all aggregations applied to Model in LIFO order."""
        while self._aggregators:
            aggregator = self._aggregators.pop(-1)  # last item
            aggregator.disaggregate(self)

    def get_content_counts(self) -> dict[str, Counter]:
        """Return number of objects stored in model organized into concepts and types."""
        data_values = self.get_data().values()
        counts = {
            "components": Counter(),
            "timevectors": Counter(),
            "curves": Counter(),
            "expressions": Counter(),
        }
        for obj in data_values:
            if isinstance(obj, Component):
                key = "components"
            elif isinstance(obj, TimeVector):
                key = "timevectors"
            elif isinstance(obj, Curve):
                key = "curves"
            elif isinstance(obj, Expr):
                key = "expressions"
            else:
                key = "unexpected"
                if key not in counts:
                    counts[key] = Counter()
            counts[key][type(obj).__name__] += 1

        assert len(data_values) == sum(c.total() for c in counts.values())

        counts["aggregators"] = Counter()
        for a in self._aggregators:
            counts["aggregators"][type(a).__name__] += 1

        return counts
