"""Token usage data storage."""

import json
from pathlib import Path
from typing import Any

from tokenash.models import UsageHistory


class Storage:
    """Manages persistent storage of usage data."""

    def __init__(self, data_dir: Path | str = "data"):
        """Initialize storage with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.usage_file = self.data_dir / "usage.json"

    def load_usage_history(self) -> UsageHistory:
        """Load usage history from file."""
        if not self.usage_file.exists():
            return UsageHistory()

        try:
            with open(self.usage_file) as f:
                data = json.load(f)
            return UsageHistory.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            # Corrupted file, start fresh
            return UsageHistory()

    def save_usage_history(self, history: UsageHistory) -> None:
        """Save usage history to file."""
        with open(self.usage_file, "w") as f:
            json.dump(history.to_dict(), f, indent=2)

    def load_chart_template(self) -> str | None:
        """Load custom chart template if exists."""
        template_file = self.data_dir / "chart_template.svg"
        if template_file.exists():
            return template_file.read_text()
        return None
