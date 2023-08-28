"""Constants for cvmfsscraper."""

import enum


class GeoAPIStatus(enum.Enum):
    """Enum for GeoAPI status."""

    OK = 0
    LOCATION_ERROR = 1
    NO_RESPONSE = 2
    NOT_FOUND = 9

    def __str__(self) -> str:
        """Custom string representation.

        This only returns the name of the enum, not the class.
        """
        return f"{self.name} ({self.value})"
