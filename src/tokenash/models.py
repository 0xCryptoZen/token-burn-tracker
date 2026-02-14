"""Token usage data models."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class DailyUsage:
    """Single day's token usage across all providers."""

    date: str  # YYYY-MM-DD format
    providers: dict[str, int] = field(default_factory=dict)  # provider_name -> token_count

    @property
    def total(self) -> int:
        """Total tokens across all providers."""
        return sum(self.providers.values())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date,
            "providers": self.providers,
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DailyUsage":
        """Create from dictionary."""
        return cls(date=data["date"], providers=data.get("providers", {}))


@dataclass
class UsageHistory:
    """Historical token usage data."""

    records: list[DailyUsage] = field(default_factory=list)

    def add_or_update(self, daily_usage: DailyUsage) -> None:
        """Add or update a day's usage record."""
        for i, record in enumerate(self.records):
            if record.date == daily_usage.date:
                # Update existing record
                for provider, count in daily_usage.providers.items():
                    record.providers[provider] = count
                return
        # Add new record
        self.records.append(daily_usage)
        # Keep sorted by date
        self.records.sort(key=lambda x: x.date)

    def get_last_n_days(self, n: int) -> list[DailyUsage]:
        """Get the last n days of usage records."""
        return self.records[-n:] if len(self.records) > n else self.records

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "records": [r.to_dict() for r in self.records],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsageHistory":
        """Create from dictionary."""
        records = [DailyUsage.from_dict(r) for r in data.get("records", [])]
        return cls(records=records)
