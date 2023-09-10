"""Exceptions for cvmfsscraper."""

from typing import Any


class CVMFSScraperBaseException(Exception):
    """Base exception for cvmfsscraper."""

    def __init__(
        self, message: str, original_excption: Exception = None, *args: Any
    ) -> None:
        """Initialize the exception."""
        self.message = message
        self.original_exception = original_excption
        super().__init__(message, *args)


class CVMFSParseError(CVMFSScraperBaseException):
    """Raised when parsing fails."""


class CVMFSValueError(CVMFSScraperBaseException):
    """Raised when a value is invalid."""


class CVMFSValidationError(CVMFSScraperBaseException):
    """Raised when a model fails validation."""


class CVMSFSServerError(CVMFSScraperBaseException):
    """Raised when the CVMFS server returns an error."""


class CVMFSFetchError(CVMFSScraperBaseException):
    """Raised when fetching a file fails."""
