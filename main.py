"""
Main entry point for Vietnam Gold Dashboard.
Fetches data every 10 minutes and displays in Rich terminal UI.
"""

import time
import warnings
from datetime import datetime
from rich.console import Console
from rich.live import Live

from repositories import GoldRepository, CurrencyRepository, CryptoRepository, StockRepository
from models import DashboardData
from dashboard import create_dashboard_table

warnings.filterwarnings("ignore", message="Unverified HTTPS request")


def fetch_all_data() -> DashboardData:
    """
    Fetch data from all repositories with error handling.
    
    Each repository is tried independently; if one fails, others continue.
    Cache decorator ensures stale data is returned if source is unavailable.
    """
    data = DashboardData()
    
    console = Console()
    
    try:
        data.gold = GoldRepository().fetch()
        console.log("[green]✓[/green] Gold price fetched")
    except Exception as e:
        console.log(f"[yellow]⚠[/yellow] Gold fetch failed: {e}")
    
    try:
        data.usd_vnd = CurrencyRepository().fetch()
        console.log("[green]✓[/green] USD/VND rate fetched")
    except Exception as e:
        console.log(f"[yellow]⚠[/yellow] USD/VND fetch failed: {e}")
    
    try:
        data.bitcoin = CryptoRepository().fetch()
        console.log("[green]✓[/green] Bitcoin price fetched")
    except Exception as e:
        console.log(f"[yellow]⚠[/yellow] Bitcoin fetch failed: {e}")
    
    try:
        data.vn30 = StockRepository().fetch()
        console.log("[green]✓[/green] VN30 index fetched")
    except Exception as e:
        console.log(f"[yellow]⚠[/yellow] VN30 fetch failed: {e}")
    
    return data


def main():
    """
    Main loop: fetch data and display dashboard with 10-minute refresh.
    """
    console = Console()
    console.print("\n[bold cyan]Vietnam Gold Dashboard Starting...[/bold cyan]\n")
    
    refresh_interval = 600
    
    while True:
        console.print(f"\n[dim]Fetching data at {datetime.now().strftime('%H:%M:%S')}...[/dim]")
        
        data = fetch_all_data()
        
        table = create_dashboard_table(data)
        console.print("\n")
        console.print(table)
        console.print(f"\n[dim italic]Next refresh in {refresh_interval // 60} minutes. Press Ctrl+C to exit.[/dim italic]\n")
        
        try:
            time.sleep(refresh_interval)
        except KeyboardInterrupt:
            raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[bold cyan]✓ Dashboard stopped[/bold cyan]")
