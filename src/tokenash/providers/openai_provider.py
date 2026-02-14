"""OpenAI API provider for token usage tracking."""

import os
from datetime import date, timedelta
from typing import Any

import requests

from tokenash.providers.base import Provider, UsageData


class OpenAIProvider(Provider):
    """Fetches token usage from OpenAI API."""

    name = "openai"
    BASE_URL = "https://api.openai.com/v1"

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        """Make authenticated request to OpenAI API."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(
            f"{self.BASE_URL}{endpoint}", headers=headers, params=params, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_daily_usage(self, start_date: date, end_date: date) -> list[UsageData]:
        """
        Fetch daily token usage from OpenAI.

        Note: OpenAI's usage API provides aggregated data. We fetch it day by day.
        """
        if not self.is_configured():
            return []

        usage_data = []
        current_date = start_date

        while current_date <= end_date:
            try:
                # OpenAI usage API endpoint
                # https://platform.openai.com/docs/api-reference/usage
                result = self._make_request(
                    "/usage",
                    {
                        "date": current_date.isoformat(),
                    },
                )

                # Aggregate all usage for the day
                total_input = 0
                total_output = 0

                # The API returns usage grouped by different dimensions
                for item in result.get("data", []):
                    total_input += item.get("n_context_tokens_total", 0)
                    total_output += item.get("n_generated_tokens_total", 0)

                if total_input > 0 or total_output > 0:
                    usage_data.append(
                        UsageData(
                            date=current_date.isoformat(),
                            input_tokens=total_input,
                            output_tokens=total_output,
                            total_tokens=total_input + total_output,
                        )
                    )

            except requests.RequestException:
                # If we can't get data for a specific day, skip it
                pass

            current_date += timedelta(days=1)

        return usage_data
