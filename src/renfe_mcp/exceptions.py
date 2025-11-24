"""
Exception hierarchy for Renfe MCP Server.

Provides a consistent set of exceptions for error handling across the application.
"""

from typing import Optional, Dict, Any


class RenfeMCPError(Exception):
    """
    Base exception for all Renfe MCP errors.

    All custom exceptions should inherit from this class to allow
    catching all application-specific errors with a single except clause.
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            code: Machine-readable error code (e.g., "STATION_NOT_FOUND")
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (code={self.code}, details={self.details})"
        return f"{self.message} (code={self.code})"


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigurationError(RenfeMCPError):
    """Raised when configuration is invalid or missing."""
    pass


# ============================================================================
# Authentication & Authorization Errors
# ============================================================================

class AuthenticationError(RenfeMCPError):
    """Base class for authentication errors."""
    pass


class InvalidAPIKeyError(AuthenticationError):
    """Raised when an invalid API key is provided."""

    def __init__(self, message: str = "Invalid API key provided"):
        super().__init__(message, code="INVALID_API_KEY")


class MissingAPIKeyError(AuthenticationError):
    """Raised when no API key is provided but required."""

    def __init__(self, message: str = "API key is required but not provided"):
        super().__init__(message, code="MISSING_API_KEY")


class RateLimitError(RenfeMCPError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        limit: int,
        window: str,
        retry_after: Optional[int] = None
    ):
        details = {
            "limit": limit,
            "window": window,
        }
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", details=details)
        self.limit = limit
        self.window = window
        self.retry_after = retry_after


# ============================================================================
# Station Errors
# ============================================================================

class StationError(RenfeMCPError):
    """Base class for station-related errors."""
    pass


class StationNotFoundError(StationError):
    """Raised when a station cannot be found."""

    def __init__(self, station_name: str, suggestions: Optional[list] = None):
        message = f"Station not found: '{station_name}'"
        details = {"station_name": station_name}
        if suggestions:
            details["suggestions"] = suggestions
            message += f". Did you mean: {', '.join(suggestions[:3])}?"
        super().__init__(message, code="STATION_NOT_FOUND", details=details)
        self.station_name = station_name
        self.suggestions = suggestions


class AmbiguousStationError(StationError):
    """Raised when a station name matches multiple stations."""

    def __init__(self, station_name: str, matches: list):
        message = f"Ambiguous station name: '{station_name}' matches {len(matches)} stations"
        super().__init__(
            message,
            code="AMBIGUOUS_STATION",
            details={"station_name": station_name, "matches": matches}
        )
        self.station_name = station_name
        self.matches = matches


class StationDataError(StationError):
    """Raised when station data is incomplete or invalid."""

    def __init__(self, station_name: str, missing_data: str):
        message = f"Station '{station_name}' is missing {missing_data}"
        super().__init__(
            message,
            code="STATION_DATA_ERROR",
            details={"station_name": station_name, "missing_data": missing_data}
        )


# ============================================================================
# Schedule Errors
# ============================================================================

class ScheduleError(RenfeMCPError):
    """Base class for schedule-related errors."""
    pass


class NoTrainsFoundError(ScheduleError):
    """Raised when no trains are found for the given search criteria."""

    def __init__(
        self,
        origin: str,
        destination: str,
        date: str,
        reason: Optional[str] = None
    ):
        message = f"No trains found from {origin} to {destination} on {date}"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            code="NO_TRAINS_FOUND",
            details={
                "origin": origin,
                "destination": destination,
                "date": date,
                "reason": reason
            }
        )


class InvalidDateError(ScheduleError):
    """Raised when an invalid date is provided."""

    def __init__(self, date_string: str, reason: Optional[str] = None):
        message = f"Invalid date: '{date_string}'"
        if reason:
            message += f". {reason}"
        super().__init__(
            message,
            code="INVALID_DATE",
            details={"date_string": date_string}
        )
        self.date_string = date_string


class DateOutOfRangeError(ScheduleError):
    """Raised when a date is outside the valid schedule range."""

    def __init__(self, date: str, min_date: str, max_date: str):
        message = f"Date {date} is outside schedule range ({min_date} to {max_date})"
        super().__init__(
            message,
            code="DATE_OUT_OF_RANGE",
            details={
                "date": date,
                "min_date": min_date,
                "max_date": max_date
            }
        )


# ============================================================================
# Price/Scraping Errors
# ============================================================================

class ScraperError(RenfeMCPError):
    """Base class for web scraping errors."""
    pass


class NetworkError(ScraperError):
    """Raised when a network error occurs during scraping."""

    def __init__(self, message: str, url: Optional[str] = None):
        details = {}
        if url:
            details["url"] = url
        super().__init__(message, code="NETWORK_ERROR", details=details)


class ScraperTimeoutError(ScraperError):
    """Raised when scraping times out."""

    def __init__(self, timeout_seconds: int):
        message = f"Request timed out after {timeout_seconds} seconds"
        super().__init__(
            message,
            code="SCRAPER_TIMEOUT",
            details={"timeout_seconds": timeout_seconds}
        )


class ParseError(ScraperError):
    """Raised when response parsing fails."""

    def __init__(self, message: str, response_preview: Optional[str] = None):
        details = {}
        if response_preview:
            details["response_preview"] = response_preview[:200]
        super().__init__(message, code="PARSE_ERROR", details=details)


class DWRTokenError(ScraperError):
    """Raised when DWR token extraction fails."""

    def __init__(self, message: str = "Failed to extract DWR token"):
        super().__init__(message, code="DWR_TOKEN_ERROR")


class PriceUnavailableError(ScraperError):
    """Raised when prices cannot be retrieved."""

    def __init__(self, origin: str, destination: str, date: str, reason: str):
        message = f"Prices unavailable for {origin} to {destination} on {date}: {reason}"
        super().__init__(
            message,
            code="PRICE_UNAVAILABLE",
            details={
                "origin": origin,
                "destination": destination,
                "date": date,
                "reason": reason
            }
        )


# ============================================================================
# Data Errors
# ============================================================================

class DataError(RenfeMCPError):
    """Base class for data-related errors."""
    pass


class GTFSDataError(DataError):
    """Raised when GTFS data is invalid or missing."""

    def __init__(self, message: str, file_name: Optional[str] = None):
        details = {}
        if file_name:
            details["file_name"] = file_name
        super().__init__(message, code="GTFS_DATA_ERROR", details=details)


class DataUpdateError(DataError):
    """Raised when data update fails."""

    def __init__(self, message: str, source_url: Optional[str] = None):
        details = {}
        if source_url:
            details["source_url"] = source_url
        super().__init__(message, code="DATA_UPDATE_ERROR", details=details)


# ============================================================================
# Security Errors
# ============================================================================

class SecurityError(RenfeMCPError):
    """Base class for security-related errors."""
    pass


class ZipSlipError(SecurityError):
    """Raised when a Zip Slip attack is detected."""

    def __init__(self, file_path: str):
        message = f"Zip Slip attack detected: path traversal in '{file_path}'"
        super().__init__(
            message,
            code="ZIP_SLIP_ATTACK",
            details={"file_path": file_path}
        )


class HTTPSecurityError(SecurityError):
    """Raised when HTTP security validation fails."""

    def __init__(self, message: str, url: Optional[str] = None):
        details = {}
        if url:
            details["url"] = url
        super().__init__(message, code="HTTP_SECURITY_ERROR", details=details)


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(RenfeMCPError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: Any, reason: str):
        message = f"Invalid value for '{field}': {reason}"
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={
                "field": field,
                "value": str(value),
                "reason": reason
            }
        )
        self.field = field
        self.value = value
        self.reason = reason
