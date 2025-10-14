from datetime import datetime, timedelta

from framcore.timeindexes.SinglePeriodTimeIndex import SinglePeriodTimeIndex  # NB! full import path needed for inheritance to work


class ConstantTimeIndex(SinglePeriodTimeIndex):
    """
    ConstantTimeIndex that is constant over time. For use in ConstantTimeVector.

    Represents a period of 52 weeks starting from the iso calendar week 1 of 1985. Extrapolates both first and last point.

    """

    def __init__(self) -> None:
        """Initialize ConstantTimeIndex."""
        super().__init__(
            start_time=datetime.fromisocalendar(1985, 1, 1),
            period_duration=timedelta(weeks=52),
            is_52_week_years=True,
            extrapolate_first_point=True,
            extrapolate_last_point=True,
        )
