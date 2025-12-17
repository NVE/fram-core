from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framcore.loaders import Loader


class TargetBound:
    """Target boundary attribute. Can be penalized if deviation from target."""

    # TODO: Implement and comment

    def add_loaders(self, loaders: set[Loader]) -> None:
        """Add all loaders stored in attributes to loaders."""
        return
