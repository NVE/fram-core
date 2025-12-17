from framcore.attributes import ReservoirCurve, StockVolume
from framcore.attributes.Storage import Storage


class HydroReservoir(Storage):
    """Represent a hydro reservoir of a HydroModule."""

    def __init__(
        self,
        capacity: StockVolume,
        reservoir_curve: ReservoirCurve = None,
        volume: StockVolume | None = None,
    ) -> None:
        """
        Initialize a HydroReservoir instance.

        Args:
            capacity (StockVolume): The maximum storage capacity of the reservoir.
            reservoir_curve (ReservoirCurve, optional): The curve describing water level elevation to volume characteristics.
            volume (StockVolume, optional): Volume of water in the reservoir.

        """
        super().__init__(
            capacity=capacity,
            reservoir_curve=reservoir_curve,
            volume=volume,
        )
