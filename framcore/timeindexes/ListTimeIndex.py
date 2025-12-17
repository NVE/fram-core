import functools
import math
from datetime import datetime, timedelta, tzinfo

import numpy as np
from numpy.typing import NDArray

from framcore.fingerprints import Fingerprint
from framcore.timeindexes import FixedFrequencyTimeIndex, TimeIndex
from framcore.timeindexes._time_vector_operations import period_duration


class ListTimeIndex(TimeIndex):
    """
    ListTimeIndex class for TimeIndexes with a list of timestamps. Subclass of TimeIndex.

    This TimeIndex is defined by a list of timestamps, with possible irregular intervals.The last timestamp is not
    necessarily the end of the time vector, and the first timestamp is not necessarily the start of the time vector
    if extrapolation is enabled.

    ListTimeIndex is not recommended for large time vectors, as it is less efficient.
    """

    def __init__(
        self,
        datetime_list: list[datetime],
        is_52_week_years: bool,
        extrapolate_first_point: bool,
        extrapolate_last_point: bool,
    ) -> None:
        """
        Initialize the ListTimeIndex class.

        Args:
            datetime_list (list[datetime]): List of datetime objects defining the time index. Must be ordered and contain more than one element.
            is_52_week_years (bool): Whether to use 52-week years. If False, full iso calendar years are used.
            extrapolate_first_point (bool): Whether to extrapolate the first point.
            extrapolate_last_point (bool): Whether to extrapolate the last point.

        Raises:
            ValueError: If datetime_list has less than two elements or is not ordered.

        """
        dts = datetime_list
        if len(dts) <= 1:
            msg = f"datetime_list must contain more than one element. Got {datetime_list}"
            raise ValueError(msg)
        if not all(dts[i] < dts[i + 1] for i in range(len(dts) - 1)):
            msg = f"All elements of datetime_list must be smaller/lower than the succeeding element. Dates must be ordered. Got {datetime_list}."
            raise ValueError(msg)
        if len(set(dt.tzinfo for dt in dts if dt is not None)) > 1:
            msg = f"Datetime objects in datetime_list have differing time zone information: {set(dt.tzinfo for dt in dts if dt is not None)}"
            raise ValueError(msg)
        if is_52_week_years and any(dts[i].isocalendar().week == 53 for i in range(len(dts))):  # noqa: PLR2004
            msg = "When is_52_week_years is True, datetime_list should not contain week 53 datetimes."
            raise ValueError(msg)

        self._datetime_list = datetime_list
        self._is_52_week_years = is_52_week_years
        self._extrapolate_first_point = extrapolate_first_point
        self._extrapolate_last_point = extrapolate_last_point

    def __eq__(self, other) -> bool:  # noqa: ANN001
        """Check if two ListTimeIndexes are equal."""
        if not isinstance(other, type(self)):
            return False
        return (
            self._datetime_list == other._datetime_list
            and self._extrapolate_first_point == other._extrapolate_first_point
            and self._extrapolate_last_point == other._extrapolate_last_point
        )

    def __hash__(self) -> int:
        """Return the hash of the ListTimeIndex."""
        return hash(
            (
                tuple(self._datetime_list),
                self._extrapolate_first_point,
                self._extrapolate_last_point,
            ),
        )

    def __repr__(self) -> str:
        """Return the string representation of the ListTimeIndex."""
        return (
            "ListTimeIndex("
            f"datetimelist={self._datetime_list}, "
            f"extrapolate_first_point={self._extrapolate_first_point}, "
            f"extrapolate_last_point={self._extrapolate_last_point})"
        )

    def get_fingerprint(self) -> Fingerprint:
        """Get the fingerprint of the ListTimeIndex."""
        fingerprint = Fingerprint()
        fingerprint.add("datetime_list", self._datetime_list)
        fingerprint.add("is_52_week_years", self._is_52_week_years)
        fingerprint.add("extrapolate_first_point", self._extrapolate_first_point)
        fingerprint.add("extrapolate_last_point", self._extrapolate_last_point)
        return fingerprint

    def get_datetime_list(self) -> list[datetime]:
        """Get a list of all periods (num_periods + 1 datetimes)."""
        return self._datetime_list.copy()

    def get_timezone(self) -> tzinfo | None:
        """Get the timezone of the TimeIndex."""
        return self._datetime_list[0].tzinfo

    def get_num_periods(self) -> int:
        """Get the number of periods in the TimeIndex."""
        return len(self._datetime_list) - 1

    def is_52_week_years(self) -> bool:
        """Check if the TimeIndex is based on 52-week years."""
        return self._is_52_week_years

    def is_one_year(self) -> bool:
        """Return True if exactly one whole year."""
        if self._extrapolate_first_point or self._extrapolate_last_point:
            return False
        start_time = self._datetime_list[0]
        stop_time = self._datetime_list[-1]
        start_year, start_week, start_weekday = start_time.isocalendar()

        if not start_weekday == start_week == 1:
            return False

        if self._is_52_week_years:
            expected_stop_time = start_time + timedelta(weeks=52)
            if expected_stop_time.isocalendar().week == 53:  # noqa: PLR2004
                expected_stop_time += timedelta(weeks=1)
            return stop_time == expected_stop_time

        stop_year, stop_week, stop_weekday = stop_time.isocalendar()
        return (start_year + 1 == stop_year) and (stop_weekday == stop_week == 1)

    def is_whole_years(self) -> bool:
        """Return True if index covers one or more full years."""
        start_time = self._datetime_list[0]
        _, start_week, start_weekday = start_time.isocalendar()

        if not start_week == start_weekday == 1:
            return False

        stop_time = self._datetime_list[-1]

        if not self.is_52_week_years():
            _, stop_week, stop_weekday = stop_time.isocalendar()
            return stop_week == stop_weekday == 1

        total_period = self.total_duration()
        total_seconds = int(total_period.total_seconds())
        seconds_per_year = 52 * 7 * 24 * 3600

        return total_seconds % seconds_per_year == 0

    def extrapolate_first_point(self) -> bool:
        """Check if the TimeIndex should extrapolate the first point."""
        return self._extrapolate_first_point

    def extrapolate_last_point(self) -> bool:
        """Check if the TimeIndex should extrapolate the last point."""
        return self._extrapolate_last_point

    def get_period_average(self, vector: NDArray, start_time: datetime, duration: timedelta, is_52_week_years: bool) -> float:
        """Get the average over the period from the vector."""
        self._check_type(vector, np.ndarray)
        self._check_type(start_time, datetime)
        self._check_type(duration, timedelta)
        self._check_type(is_52_week_years, bool)

        if vector.shape != (self.get_num_periods(),):
            msg = f"Vector shape {vector.shape} does not match number of periods {self.get_num_periods()} of timeindex ({self})."
            raise ValueError(msg)

        if not self.extrapolate_first_point():
            if start_time < self._datetime_list[0]:
                msg = f"start_time {start_time} is before start of timeindex {self._datetime_list[0]}, and extrapolate_first_point is False."
                raise ValueError(msg)
            if (start_time + duration) < self._datetime_list[0]:
                msg = f"End time {start_time + duration} is before start of timeindex {self._datetime_list[0]}, and extrapolate_first_point is False."
                raise ValueError(msg)

        if not self.extrapolate_last_point():
            if (start_time + duration) > self._datetime_list[-1]:
                msg = f"End time {start_time + duration} is after end of timeindex {self._datetime_list[-1]}, and extrapolate_last_point is False."
                raise ValueError(msg)
            if start_time > self._datetime_list[-1]:
                msg = f"start_time {start_time} is after end of timeindex {self._datetime_list[-1]}, and extrapolate_last_point is False."
                raise ValueError(msg)

        target_timeindex = FixedFrequencyTimeIndex(
            start_time=start_time,
            period_duration=duration,
            num_periods=1,
            is_52_week_years=is_52_week_years,
            extrapolate_first_point=self.extrapolate_first_point(),
            extrapolate_last_point=self.extrapolate_last_point(),
        )

        target_vector = np.zeros(1, dtype=vector.dtype)
        self.write_into_fixed_frequency(
            target_vector=target_vector,
            target_timeindex=target_timeindex,
            input_vector=vector,
        )
        return target_vector[0]

    def write_into_fixed_frequency(
        self,
        target_vector: NDArray,
        target_timeindex: FixedFrequencyTimeIndex,
        input_vector: NDArray,
    ) -> None:
        """Write the input vector into the target vector using the target FixedFrequencyTimeIndex."""
        self._check_type(target_vector, np.ndarray)
        self._check_type(target_timeindex, FixedFrequencyTimeIndex)
        self._check_type(input_vector, np.ndarray)

        dts: list[datetime] = self._datetime_list

        durations = set(self._microseconds(period_duration(dts[i], dts[i + 1], self._is_52_week_years)) for i in range(len(dts) - 1))
        smallest_common_period_duration = functools.reduce(math.gcd, durations)

        num_periods_ff = self._microseconds(self.total_duration()) // smallest_common_period_duration
        input_vector_ff = np.zeros(num_periods_ff, dtype=target_vector.dtype)

        i_start_ff = 0
        for i in range(len(dts) - 1):
            num_periods = self._microseconds(period_duration(dts[i], dts[i + 1], self._is_52_week_years)) // smallest_common_period_duration
            i_stop_ff = i_start_ff + num_periods
            input_vector_ff[i_start_ff:i_stop_ff] = input_vector[i]
            i_start_ff = i_stop_ff

        input_timeindex_ff = FixedFrequencyTimeIndex(
            start_time=dts[0],
            num_periods=num_periods_ff,
            period_duration=timedelta(microseconds=smallest_common_period_duration),
            is_52_week_years=self.is_52_week_years(),
            extrapolate_first_point=self.extrapolate_first_point(),
            extrapolate_last_point=self.extrapolate_last_point(),
        )

        input_timeindex_ff.write_into_fixed_frequency(
            target_vector=target_vector,
            target_timeindex=target_timeindex,
            input_vector=input_vector_ff,
        )

    def total_duration(self) -> timedelta:
        """
        Return the total duration covered by the time index.

        Returns
        -------
        timedelta
            The duration from the first to the last datetime in the index, skipping all weeks 53 periods if 52-week time format.

        """
        start_time = self._datetime_list[0]
        end_time = self._datetime_list[-1]
        return period_duration(start_time, end_time, self.is_52_week_years())

    def _microseconds(self, duration: timedelta) -> int:
        return int(duration.total_seconds() * 1e6)

    def is_constant(self) -> bool:
        """
        Return True if the time index is constant (single period and both extrapolation flags are True).

        Returns
        -------
        bool
            True if the time index is constant, False otherwise.

        """
        return self.get_num_periods() == 1 and self.extrapolate_first_point() == self.extrapolate_last_point() is True
