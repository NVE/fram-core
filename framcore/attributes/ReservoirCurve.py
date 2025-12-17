from __future__ import annotations

from typing import TYPE_CHECKING

from framcore import Base

if TYPE_CHECKING:
    from framcore.loaders import Loader


class ReservoirCurve(Base):
    """Water level elevation to water volume characteristics for HydroStorage."""

    # TODO: Implement and comment, also too generic name

    def __init__(self, value: str | None) -> None:
        """Initialize a ReservoirCurve instance."""
        self._check_type(value, (str, type(None)))
        self._value = value

    def add_loaders(self, loaders: set[Loader]) -> None:
        """Add all loaders stored in attributes to loaders."""
        return
