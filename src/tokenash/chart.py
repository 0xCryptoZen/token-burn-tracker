"""Chart generation using QuickChart.io API."""

import requests
from datetime import datetime
from pathlib import Path
from typing import Any

from tokenash.models import DailyUsage


class ChartGenerator:
    """Generates token usage charts using QuickChart.io."""

    QUICKCHART_URL = "https://quickchart.io/chart"

    def __init__(
        self,
        title: str = "🔥 Token Consumption (Last 30 Days)",
        width: int = 800,
        height: int = 400,
        output_dir: Path | str = "charts",
    ):
        self.title = title
        self.width = width
        self.height = height
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _format_number(self, num: int) -> str:
        """Format large numbers with K/M suffix."""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.0f}K"
        return str(num)

    def _build_chart_config(self, usage_data: list[DailyUsage]) -> dict[str, Any]:
        """Build QuickChart configuration."""
        labels = []
        totals = []
        provider_data: dict[str, list[int]] = {}

        for day in usage_data:
            date_obj = datetime.strptime(day.date, "%Y-%m-%d")
            labels.append(date_obj.strftime("%m/%d"))
            totals.append(day.total)

            for provider, count in day.providers.items():
                if provider not in provider_data:
                    provider_data[provider] = []
                provider_data[provider].append(count)

        datasets = []
        provider_colors = {
            "openai": {"bg": "rgba(16, 163, 127, 0.7)", "border": "rgba(16, 163, 127, 1)"},
            "anthropic": {"bg": "rgba(204, 131, 75, 0.7)", "border": "rgba(204, 131, 75, 1)"},
        }

        if provider_data:
            for provider, data in provider_data.items():
                colors = provider_colors.get(
                    provider, {"bg": "rgba(100, 100, 100, 0.7)", "border": "rgba(100, 100, 100, 1)"}
                )
                datasets.append(
                    {
                        "label": provider.capitalize(),
                        "data": data,
                        "backgroundColor": colors["bg"],
                        "borderColor": colors["border"],
                        "borderWidth": 1,
                    }
                )
        else:
            datasets = [
                {
                    "label": "Total Tokens",
                    "data": totals,
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "borderWidth": 2,
                    "fill": True,
                    "tension": 0.3,
                }
            ]

        total_tokens = sum(totals)
        avg_tokens = total_tokens // len(totals) if totals else 0
        max_tokens = max(totals) if totals else 0

        chart_config = {
            "type": "bar" if provider_data else "line",
            "data": {
                "labels": labels,
                "datasets": datasets,
            },
            "options": {
                "title": {
                    "display": True,
                    "text": f"{self.title}\nTotal: {self._format_number(total_tokens)} | Avg: {self._format_number(avg_tokens)}/day | Peak: {self._format_number(max_tokens)}",
                    "fontSize": 16,
                },
                "scales": {
                    "xAxes": [{"stacked": True}],
                    "yAxes": [
                        {
                            "stacked": True,
                            "ticks": {
                                "callback": "function(value) { return value >= 1000 ? (value/1000) + 'K' : value; }",
                            },
                            "scaleLabel": {
                                "display": True,
                                "labelString": "Tokens",
                            },
                        }
                    ],
                },
                "legend": {
                    "display": len(datasets) > 1,
                    "position": "bottom",
                },
                "plugins": {
                    "datalabels": {
                        "display": False,
                    }
                },
            },
        }

        return chart_config

    def generate_chart_url(self, usage_data: list[DailyUsage]) -> str:
        """Generate QuickChart URL for the chart."""
        config = self._build_chart_config(usage_data)
        import json
        from urllib.parse import quote

        config_str = json.dumps(config, separators=(",", ":"))
        return (
            f"{self.QUICKCHART_URL}?c={quote(config_str)}&width={self.width}&height={self.height}"
        )

    def generate_chart_image(
        self, usage_data: list[DailyUsage], filename: str = "token_usage.png"
    ) -> Path | None:
        """Download chart as PNG image."""
        if not usage_data:
            return None

        url = self.generate_chart_url(usage_data)

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            output_path = self.output_dir / filename
            with open(output_path, "wb") as f:
                f.write(response.content)

            return output_path
        except requests.RequestException:
            return None

    def generate_markdown(self, usage_data: list[DailyUsage], include_image: bool = True) -> str:
        """Generate markdown snippet for GitHub README."""
        if not usage_data:
            return "<!-- TokenAsh: No usage data available -->\n"

        chart_url = self.generate_chart_url(usage_data)

        total_tokens = sum(d.total for d in usage_data)
        avg_tokens = total_tokens // len(usage_data) if usage_data else 0

        lines = [
            "## 🔥 Token Consumption",
            "",
            f"![Token Usage Chart]({chart_url})",
            "",
            f"> **Total (30d):** {self._format_number(total_tokens)} tokens | **Daily Avg:** {self._format_number(avg_tokens)} tokens",
            "",
            f"<sub>🔄 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC | Generated by [TokenAsh](https://github.com/bond/token-burn-tracker)</sub>",
            "",
        ]

        return "\n".join(lines)
