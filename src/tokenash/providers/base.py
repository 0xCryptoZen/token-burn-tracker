"""Base provider interface for token usage APIs."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class UsageData:
    """Token usage data from a provider."""

    date: str  # YYYY-MM-DD
    input_tokens: int
    output_tokens: int
    total_tokens: int


class Provider(ABC):
    """Abstract base class for token usage providers."""

    name: str = "base"

    def __init__(self, api_key: str | None = None):
        """Initialize provider with optional API key."""
        self.api_key = api_key

    @abstractmethod
    def get_daily_usage(self, start_date: date, end_date: date) -> list[UsageData]:
        """
        Fetch daily token usage for the given date range.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            List of UsageData objects, one per day
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        pass
