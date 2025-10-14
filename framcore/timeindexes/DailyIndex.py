from datetime import timedelta

from framcore.timeindexes.ProfileTimeIndex import ProfileTimeIndex  # NB! full import path needed for inheritance to work


class DailyIndex(ProfileTimeIndex):
    """
    ProfileTimeIndex with one or more whole years with daily resolution. Either years with 52 weeks or full iso calendar years.

    No extrapolation inherited from ProfileTimeIndex.
    """

    def __init__(
        self,
        start_year: int,
        num_years: int,
        is_52_week_years: bool = True,
    ) -> None:
        """
        Initialize DailyIndex over a number of years. Either years with 52 weeks or full iso calendar years.

        Args:
            start_year (int): First year in the index.
            num_years (int): Number of years in the index.
            is_52_week_years (bool, optional): Whether to use 52-week years. If False, full iso calendar years are used. Defaults to True.

        """
        super().__init__(
            start_year=start_year,
            num_years=num_years,
            period_duration=timedelta(days=1),
            is_52_week_years=is_52_week_years,
        )
