"""
Rich terminal dashboard UI for Vietnam Gold Dashboard.
Displays gold, currency, crypto, and stock data with color-coded freshness indicators.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict

from .models import DashboardData, GoldPrice, UsdVndRate, BitcoinPrice, Vn30Index, AssetHistoricalData


def format_vn_number(value: Decimal, decimal_places: int = 0) -> str:
    """
    Convert Decimal back to Vietnamese display format.
    
    Examples:
        25500000 -> 25.500.000
        1234.56 -> 1.234,56
    """
    if value is None:
        return "N/A"
    
    value_str = str(value)
    
    if '.' in value_str:
        integer_part, decimal_part = value_str.split('.')
    else:
        integer_part = value_str
        decimal_part = ""
    
    integer_part = integer_part.lstrip('-')
    is_negative = str(value).startswith('-')
    
    formatted_int = ""
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            formatted_int = "." + formatted_int
        formatted_int = digit + formatted_int
    
    if decimal_part and decimal_places > 0:
        decimal_part = decimal_part[:decimal_places]
        result = f"{formatted_int},{decimal_part}"
    else:
        result = formatted_int
    
    if is_negative:
        result = "-" + result
    
    return result


def get_status_color(timestamp: datetime) -> str:
    """
    Return color based on data freshness.
    
    Green: < 5 min old
    Yellow: 5-10 min old
    Red: > 10 min old
    """
    age = datetime.now() - timestamp
    
    if age < timedelta(minutes=5):
        return "green"
    elif age < timedelta(minutes=10):
        return "yellow"
    else:
        return "red"


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp as readable string."""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def create_dashboard_table(data: DashboardData) -> Table:
    """
    Generate Rich Table from DashboardData.
    
    Displays all 4 data sources with formatting and color-coded freshness.
    """
    table = Table(title="Vietnam Gold & Market Dashboard", show_header=False, title_style="bold cyan")
    
    table.add_column("Label", style="bold", width=20)
    table.add_column("Value", width=60)
    
    if data.gold:
        color = get_status_color(data.gold.timestamp)
        table.add_row(
            "🟡 Gold",
            Text(f"Buy: {format_vn_number(data.gold.buy_price)} {data.gold.unit}", style=color)
        )
        table.add_row(
            "",
            Text(f"Sell: {format_vn_number(data.gold.sell_price)} {data.gold.unit}", style=color)
        )
        table.add_row(
            "",
            Text(f"Source: {data.gold.source} | Updated: {format_timestamp(data.gold.timestamp)}", style="dim")
        )
    else:
        table.add_row("🟡 Gold", Text("Unavailable (fetching...)", style="red"))
    
    table.add_row("", "")
    
    if data.usd_vnd:
        color = get_status_color(data.usd_vnd.timestamp)
        table.add_row(
            "💵 USD/VND",
            Text(f"Sell Rate: {format_vn_number(data.usd_vnd.sell_rate)} VND/USD", style=color)
        )
        table.add_row(
            "",
            Text(f"Source: {data.usd_vnd.source} | Updated: {format_timestamp(data.usd_vnd.timestamp)}", style="dim")
        )
    else:
        table.add_row("💵 USD/VND", Text("Unavailable (fetching...)", style="red"))
    
    table.add_row("", "")
    
    if data.bitcoin:
        color = get_status_color(data.bitcoin.timestamp)
        table.add_row(
            "₿ Bitcoin",
            Text(f"BTC to VND: {format_vn_number(data.bitcoin.btc_to_vnd)} VND", style=color)
        )
        table.add_row(
            "",
            Text(f"Source: {data.bitcoin.source} | Updated: {format_timestamp(data.bitcoin.timestamp)}", style="dim")
        )
    else:
        table.add_row("₿ Bitcoin", Text("Unavailable (fetching...)", style="red"))
    
    table.add_row("", "")
    
    if data.vn30:
        color = get_status_color(data.vn30.timestamp)
        change_text = f" ({format_vn_number(data.vn30.change_percent, 2)}%)" if data.vn30.change_percent else ""
        table.add_row(
            "📈 VN30 Index",
            Text(f"Value: {format_vn_number(data.vn30.index_value, 2)}{change_text}", style=color)
        )
        table.add_row(
            "",
            Text(f"Source: {data.vn30.source} | Updated: {format_timestamp(data.vn30.timestamp)}", style="dim")
        )
    else:
        table.add_row("📈 VN30 Index", Text("Unavailable (fetching...)", style="red"))
    
    return table


def _format_change(percent: Optional[Decimal]) -> Text:
    """Format a percentage change with color and sign prefix."""
    if percent is None:
        return Text("--", style="dim")
    sign = "+" if percent >= 0 else ""
    color = "green" if percent >= 0 else "red"
    return Text(f"{sign}{format_vn_number(percent, 2)}%", style=color)


ASSET_LABELS = {
    "gold": "\U0001f7e1 Gold",
    "usd_vnd": "\U0001f4b5 USD/VND",
    "bitcoin": "\u20bf Bitcoin",
    "vn30": "\U0001f4c8 VN30",
}


def create_history_table(history: Dict[str, AssetHistoricalData]) -> Table:
    """
    Generate a Rich Table showing 1D/1W/1M/1Y/3Y percentage changes per asset.

    Green = positive change, Red = negative change, -- = data unavailable.
    """
    table = Table(title="Historical Changes", title_style="bold magenta")

    table.add_column("Asset", style="bold", width=16)
    table.add_column("1D", justify="right", width=10)
    table.add_column("1W", justify="right", width=12)
    table.add_column("1M", justify="right", width=12)
    table.add_column("1Y", justify="right", width=12)
    table.add_column("3Y", justify="right", width=12)

    period_order = ["1D", "1W", "1M", "1Y", "3Y"]

    for asset_key in ["gold", "usd_vnd", "bitcoin", "vn30"]:
        asset_data = history.get(asset_key)
        label = ASSET_LABELS.get(asset_key, asset_key)

        if asset_data is None:
            table.add_row(label, *[Text("--", style="dim") for _ in period_order])
            continue

        change_map = {c.period: c.change_percent for c in asset_data.changes}
        cells = [_format_change(change_map.get(p)) for p in period_order]
        table.add_row(label, *cells)

    return table


def create_dashboard_panel(
    data: DashboardData,
    next_refresh_seconds: int = 600,
    history: Optional[Dict[str, AssetHistoricalData]] = None,
) -> Panel:
    """
    Create a Rich Panel containing the dashboard table, history table, and footer.
    """
    table = create_dashboard_table(data)

    parts = [table]

    if history:
        parts.append(Text(""))  # spacer
        parts.append(create_history_table(history))

    minutes = next_refresh_seconds // 60
    seconds = next_refresh_seconds % 60
    footer_text = f"\nNext refresh in: {minutes}:{seconds:02d} | Press Ctrl+C to exit"
    parts.append(Text(footer_text, style="dim italic"))

    return Panel(
        Text.assemble(*parts),
        title="Vietnam Gold Dashboard",
        border_style="cyan"
    )
