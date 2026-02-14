"""TokenAsh - Track your AI token usage."""

import os
from datetime import date, timedelta
from pathlib import Path

import yaml

from tokenash.chart import ChartGenerator
from tokenash.models import DailyUsage, UsageHistory
from tokenash.providers import AnthropicProvider, OpenAIProvider
from tokenash.storage import Storage


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    if not Path(config_path).exists():
        return {}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def get_providers(config: dict) -> list:
    """Initialize enabled providers from config."""
    providers = []

    openai_config = config.get("openai", {})
    if openai_config.get("enabled", False):
        api_key = openai_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if api_key:
            providers.append(OpenAIProvider(api_key=api_key))

    anthropic_config = config.get("anthropic", {})
    if anthropic_config.get("enabled", False):
        api_key = anthropic_config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            providers.append(AnthropicProvider(api_key=api_key))

    return providers


def fetch_today_usage(providers: list) -> DailyUsage:
    """Fetch today's token usage from all providers."""
    today = date.today()
    usage = DailyUsage(date=today.isoformat())

    for provider in providers:
        if not provider.is_configured():
            continue

        try:
            daily_data = provider.get_daily_usage(today, today)
            if daily_data:
                usage.providers[provider.name] = daily_data[0].total_tokens
        except Exception as e:
            print(f"Error fetching {provider.name} usage: {e}")

    return usage


def fetch_historical_usage(providers: list, days: int = 30) -> list[DailyUsage]:
    """Fetch historical usage for the last N days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    usage_list = []

    for provider in providers:
        if not provider.is_configured():
            continue

        try:
            data = provider.get_daily_usage(start_date, end_date)
            for d in data:
                existing = next((u for u in usage_list if u.date == d.date), None)
                if existing:
                    existing.providers[provider.name] = d.total_tokens
                else:
                    new_usage = DailyUsage(date=d.date)
                    new_usage.providers[provider.name] = d.total_tokens
                    usage_list.append(new_usage)
        except Exception as e:
            print(f"Error fetching {provider.name} historical usage: {e}")

    usage_list.sort(key=lambda x: x.date)
    return usage_list


def update_readme(markdown: str, readme_path: str, start_marker: str, end_marker: str) -> bool:
    """Update README with new chart markdown."""
    if not Path(readme_path).exists():
        print(f"README not found at {readme_path}")
        return False

    content = Path(readme_path).read_text()

    if start_marker not in content or end_marker not in content:
        print("Markers not found in README")
        return False

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker) + len(end_marker)

    new_content = (
        content[:start_idx] + start_marker + "\n" + markdown + "\n" + end_marker + content[end_idx:]
    )

    Path(readme_path).write_text(new_content)
    return True


def run(config_path: str = "config.yaml", output_dir: str = "data", charts_dir: str = "charts"):
    """Main entry point for TokenAsh."""
    config = load_config(config_path)
    chart_config = config.get("chart", {})

    storage = Storage(output_dir)
    providers = get_providers(config)

    if not providers:
        print("No providers configured. Check your config.yaml or environment variables.")
        return

    print(f"Fetching usage from {len(providers)} provider(s)...")

    history = storage.load_usage_history()

    today_usage = fetch_today_usage(providers)
    if today_usage.providers:
        history.add_or_update(today_usage)
        storage.save_usage_history(history)
        print(f"Updated usage for {today_usage.date}")

    chart = ChartGenerator(
        title=chart_config.get("title", "🔥 Token Consumption (Last 30 Days)"),
        output_dir=charts_dir,
    )

    recent_data = history.get_last_n_days(chart_config.get("days", 30))

    if not recent_data:
        print("No usage data available")
        return

    markdown = chart.generate_markdown(recent_data)

    print("\n" + markdown)

    markdown_path = Path(charts_dir) / "token_usage.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown)
    print(f"Saved markdown to {markdown_path}")

    github_config = config.get("github", {})
    profile_repo = github_config.get("profile_repo")

    if profile_repo:
        readme_path = github_config.get("readme_path", "README.md")
        start_marker = github_config.get("section_start", "<!-- TOKENASH:START -->")
        end_marker = github_config.get("section_end", "<!-- TOKENASH:END -->")

        if update_readme(markdown, readme_path, start_marker, end_marker):
            print(f"Updated {readme_path}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="TokenAsh - Track your AI token usage")
    parser.add_argument("--config", "-c", default="config.yaml", help="Path to config file")
    parser.add_argument("--output", "-o", default="data", help="Output directory for data")
    parser.add_argument("--charts", default="charts", help="Output directory for charts")

    args = parser.parse_args()
    run(config_path=args.config, output_dir=args.output, charts_dir=args.charts)


if __name__ == "__main__":
    main()
