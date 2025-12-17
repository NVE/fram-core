from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from numpy.typing import NDArray

from framcore import Base
from framcore.fingerprints import Fingerprint
from framcore.timeindexes import TimeIndex
from framcore.timevectors import ReferencePeriod

if TYPE_CHECKING:
    from framcore.loaders import TimeVectorLoader


# TODO: Floating point precision
class TimeVector(Base, ABC):
    """TimeVector interface class for defining timeseries data."""

    def __init__(self) -> None:
        """Initialize the TimeVector class."""
        super().__init__()

    @abstractmethod
    def __eq__(self, other) -> bool:  # noqa: ANN001
        """Check if two TimeVectors are equal."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Compute hash value."""
        pass

    @abstractmethod
    def get_vector(self, is_float32: bool) -> NDArray:
        """Get the values of the TimeVector."""
        pass

    @abstractmethod
    def get_timeindex(self) -> TimeIndex | None:
        """Get the TimeIndex of the TimeVector."""
        pass

    @abstractmethod
    def is_constant(self) -> bool:
        """Check if the TimeVector is constant."""
        pass

    @abstractmethod
    def is_max_level(self) -> bool | None:
        """
        Whether the TimeVector represents the maximum level, average level given a reference period, or not a level at all.

        See LevelProfile for a description of Level (max or avg) and Profile (max one or mean one), and their formats.

        """
        pass

    @abstractmethod
    def is_zero_one_profile(self) -> bool | None:
        """
        Whether the TimeVector represents a profile with values between 0 and 1, a profile with average 1 over a given reference period, or is not a profile.

        See LevelProfile for a description of Level (max or avg) and Profile (max one or mean one), and their formats.

        """
        pass

    @abstractmethod
    def get_unit(self) -> str | None:
        """Get the unit of the TimeVector."""
        pass

    @abstractmethod
    def get_fingerprint(self) -> Fingerprint:
        """Get the fingerprint of the TimeVector."""
        pass

    @abstractmethod
    def get_reference_period(self) -> ReferencePeriod | None:
        """Get the reference period of the TimeVector."""
        pass

    @abstractmethod
    def get_loader(self) -> TimeVectorLoader | None:
        """
        Get the TimeVectorLoader of the TimeVector if self has one.

        TimeVectors can store timeseries data in Loaders that point to databases. Data is only retrieved and cached when the TimeVector is queried.
        """
        pass

    """
    Checks that the TimeVector is either a level or a profile.

    Raises:
        ValueError: If both is_max_level and is_zero_one_profile are None or both are not None.
    """

    def _check_is_level_or_profile(self) -> None:
        """Ensure that the TimeVector is either a level or a profile."""
        if (self.is_max_level() is not None and self.is_zero_one_profile() is not None) or (self.is_max_level() is None and self.is_zero_one_profile() is None):
            message = (
                f"Invalid input arguments for {self}: Must have exactly one 'non-None' value for "
                "is_max_level and is_zero_one_profile. A TimeVector is either a level or a profile."
            )
            raise ValueError(message)
