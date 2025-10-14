from datetime import datetime, timedelta

from framcore.timeindexes.SinglePeriodTimeIndex import SinglePeriodTimeIndex  # NB! full import path needed for inheritance to work


class ModelYear(SinglePeriodTimeIndex):
    """ModelYear represent a period of 52 weeks starting from the iso calendar week 1 of a specified year. No extrapolation."""

    def __init__(self, year: int) -> None:
        """
        Initialize ModelYear to a period of 52 weeks starting from the iso calendar week 1 of the specified year. No extrapolation.

        Args:
            year (int): Year to represent.

        """
        super().__init__(
            start_time=datetime.fromisocalendar(year, 1, 1),
            period_duration=timedelta(weeks=52),
            is_52_week_years=True,
            extrapolate_first_point=False,
            extrapolate_last_point=False,
        )
