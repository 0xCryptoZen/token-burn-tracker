"""Anthropic (Claude) API provider for token usage tracking."""

import os
from datetime import date, timedelta
from typing import Any

import requests

from tokenash.providers.base import Provider, UsageData


class AnthropicProvider(Provider):
    """Fetches token usage from Anthropic API."""

    name = "anthropic"
    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        """Make authenticated request to Anthropic API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        response = requests.get(
            f"{self.BASE_URL}{endpoint}", headers=headers, params=params, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_daily_usage(self, start_date: date, end_date: date) -> list[UsageData]:
        """
        Fetch daily token usage from Anthropic.

        Note: Anthropic's API may not have a direct usage endpoint like OpenAI.
        This implementation assumes a /usage endpoint exists.
        Adjust based on actual API documentation.
        """
        if not self.is_configured():
            return []

        usage_data = []

        try:
            # Try to fetch usage data from Anthropic API
            # Note: Anthropic's usage API structure may differ
            # This is a placeholder implementation
            result = self._make_request(
                "/usage",
                {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            )

            # Process the response based on actual API structure
            for day_data in result.get("data", []):
                usage_data.append(
                    UsageData(
                        date=day_data.get("date", ""),
                        input_tokens=day_data.get("input_tokens", 0),
                        output_tokens=day_data.get("output_tokens", 0),
                        total_tokens=day_data.get("total_tokens", 0),
                    )
                )

        except requests.RequestException:
            # If the API doesn't support this endpoint yet, return empty
            pass

        return usage_data
