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
from typing import Optional

from models import DashboardData, GoldPrice, UsdVndRate, BitcoinPrice, Vn30Index


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


def create_dashboard_panel(data: DashboardData, next_refresh_seconds: int = 600) -> Panel:
    """
    Create a Rich Panel containing the dashboard table and footer.
    """
    table = create_dashboard_table(data)
    
    minutes = next_refresh_seconds // 60
    seconds = next_refresh_seconds % 60
    footer_text = f"\nNext refresh in: {minutes}:{seconds:02d} | Press Ctrl+C to exit"
    
    return Panel(
        Text.assemble(table, Text(footer_text, style="dim italic")),
        title="Vietnam Gold Dashboard",
        border_style="cyan"
    )
