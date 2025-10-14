from datetime import timedelta

from framcore.timeindexes.ProfileTimeIndex import ProfileTimeIndex  # NB! full import path needed for inheritance to work


class OneYearProfileTimeIndex(ProfileTimeIndex):
    """
    ProfileTimeIndex with fixed frequency over one year of either 52 or 53 weeks. No extrapolation inherited from ProfileTimeIndex.

    Attributes:
        period_duration (timedelta): Duration of each period.
        is_52_week_years (bool): Whether to use 52-week years.

    """

    def __init__(self, period_duration: timedelta, is_52_week_years: bool) -> None:
        """
        Initialize a ProfileTimeIndex with a fixed frequency over one year.

        If is_52_week_years is True, the period_duration must divide evenly into 52 weeks. If False, it must divide evenly into 53 weeks.
        We use 1982 for 52-week years and 1981 for 53-week years.

        Args:
            period_duration (timedelta): Duration of each period.
            is_52_week_years (bool): Whether to use 52-week years.

        """
        year = 1982 if is_52_week_years else 1981
        super().__init__(year, 1, period_duration, is_52_week_years)
