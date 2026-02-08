#!/usr/bin/env python3
"""
Dynamic Ping-Pong Trading Bot v2.1.1 - ASYMMETRIC GRID + COMPOUNDING
Strategy: Asymmetric dual triggers with compounding trade sizes
Buy at -1% | Sell at +1.5% | Trade size = 5% of portfolio (grows over time!)
"""

import os
import time
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from binance.client import Client
from binance.exceptions import BinanceAPIException
from rich.console import Console
from rich.table import Table
from rich import box
import questionary
from questionary import Style
import math

# === Constants ===
BOT_NAME = "Asymmetric Grid Bot"
BOT_VERSION = "2.1.1"
LOG_DIR = "logs"

# Rich console
console = Console()

# Questionary style
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
])

# === Logger ===
class TradeLogger:
    """Handles logging to file"""
    def __init__(self, symbol: str, paper_trading: bool):
        os.makedirs(LOG_DIR, exist_ok=True)
        mode = "paper" if paper_trading else "live"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(LOG_DIR, f"{symbol}_{mode}_dual_{timestamp}.log")
        self.log_info(f"=== {BOT_NAME} v{BOT_VERSION} ===")
        self.log_info(f"Mode: {'Paper Trading' if paper_trading else 'Live Trading'}")
    
    def _write(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}\n"
        with open(self.log_file, 'a') as f:
            f.write(log_line)
    
    def log_info(self, message: str):
        self._write("INFO", message)
    
    def log_warning(self, message: str):
        self._write("WARNING", message)
    
    def log_error(self, message: str):
        self._write("ERROR", message)
    
    def log_trade(self, trade_type: str, price: float, amount: float, total: float):
        msg = f"{trade_type} | Price: ${price:.2f} | Amount: {amount:.6f} | Total: ${total:.2f}"
        self._write("TRADE", msg)

# === Configuration ===
@dataclass
class BotConfig:
    """Bot configuration"""
    api_key: str
    api_secret: str
    symbol: str
    base_asset: str
    quote_asset: str
    initial_investment: float
    usdt_per_trade: float
    paper_trading: bool

# === Banner ===
def display_banner():
    """Display ASCII art banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║    █████╗ ███████╗██╗   ██╗███╗   ███╗███╗   ███╗███████╗████████╗  ║
║   ██╔══██╗██╔════╝╚██╗ ██╔╝████╗ ████║████╗ ████║██╔════╝╚══██╔══╝  ║
║   ███████║███████╗ ╚████╔╝ ██╔████╔██║██╔████╔██║█████╗     ██║     ║
║   ██╔══██║╚════██║  ╚██╔╝  ██║╚██╔╝██║██║╚██╔╝██║██╔══╝     ██║     ║
║   ██║  ██║███████║   ██║   ██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗   ██║     ║
║   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝   ╚═╝     ║
║                                                                       ║
║            ASYMMETRIC GRID BOT v2.1.1 - SMART COMPOUNDING            ║
║                      Codename: AsymGrid-v2.1                         ║
║                                                                       ║
║   • Asymmetric Triggers (-1% / +1.5%)  • True Compounding            ║
║   • Growing Trade Sizes  • Enhanced Logging  • Paper/Live Mode       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
    console.print(f"[bold cyan]{banner}[/bold cyan]")

# === Setup Wizard ===
class SetupWizard:
    """Interactive setup wizard"""
    
    def run(self) -> BotConfig:
        display_banner()
        console.print("\n[dim]Strategy: Asymmetric Grid (-1% buy / +1.5% sell) with Compounding[/dim]\n")
        
        # Trading mode
        mode = questionary.select(
            "Select trading mode:",
            choices=["🧪 Paper Trading (Test)", "🔴 Live Trading"],
            style=custom_style
        ).ask()
        paper_trading = "Paper" in mode
        
        # Symbol selection
        symbol_choice = questionary.select(
            "Select trading pair:",
            choices=["BTC/USDT", "ETH/USDT", "SOL/USDT"],
            style=custom_style
        ).ask()
        
        if "BTC" in symbol_choice:
            symbol = "BTCUSDT"
            base_asset = "BTC"
        elif "ETH" in symbol_choice:
            symbol = "ETHUSDT"
            base_asset = "ETH"
        else:  # SOL
            symbol = "SOLUSDT"
            base_asset = "SOL"
        
        # Investment amount
        investment = float(questionary.text(
            "Enter USDT investment amount:",
            default="1000",
            style=custom_style
        ).ask())
        
        # Trade size (default 5% of investment)
        default_trade_size = int(investment * 0.05)
        usdt_per_trade = float(questionary.text(
            "Enter USDT per trade:",
            default=str(default_trade_size),
            style=custom_style
        ).ask())
        
        # API credentials
        if not paper_trading:
            console.print("\n[yellow]⚠️ API keys required for live trading[/yellow]")
            api_key = questionary.password(
                "Enter Binance API Key:",
                style=custom_style
            ).ask()
            api_secret = questionary.password(
                "Enter Binance API Secret:",
                style=custom_style
            ).ask()
        else:
            api_key = "PAPER_KEY"
            api_secret = "PAPER_SECRET"
        
        return BotConfig(
            api_key=api_key,
            api_secret=api_secret,
            symbol=symbol,
            base_asset=base_asset,
            quote_asset="USDT",
            initial_investment=investment,
            usdt_per_trade=usdt_per_trade,
            paper_trading=paper_trading
        )

# === Main Bot ===
class DualTriggerBot:
    """Dual Trigger trading bot - monitors both buy and sell triggers simultaneously"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = TradeLogger(config.symbol, config.paper_trading)
        
        # Initialize Binance client (even for paper trading, to get real prices)
        self.client = None
        if not config.paper_trading:
            self.client = Client(config.api_key, config.api_secret)
        else:
            # For paper trading, we still need price data
            self.client = Client("", "")  # Public endpoints don't need auth
        
        # Get exchange info for LOT_SIZE filters
        self.step_size = 0.0
        self.min_qty = 0.0
        self.max_qty = 0.0
        self._get_lot_size_filters()
        
        # State variables
        self.crypto_balance = 0.0
        self.usdt_balance = config.initial_investment
        self.initial_portfolio = config.initial_investment
        
        # Dual trigger state - BOTH triggers are active simultaneously
        self.reference_price = 0.0  # Reference price for calculating triggers
        self.buy_trigger = 0.0      # Buy trigger (reference * 0.99)
        self.sell_trigger = 0.0     # Sell trigger (reference * 1.015) ASYMMETRIC!
        
        # Statistics
        self.trade_count = 0
        self.cumulative_profit = 0.0
        self.last_buy_price = 0.0
        self.last_sell_price = 0.0
        
        # Track trade size for compounding visibility
        self.last_trade_size = 0.0
        self.initial_trade_size = config.initial_investment * 0.05
        
        self.logger.log_info(f"Bot initialized | Investment: ${config.initial_investment:,.2f}")
    
    def _get_lot_size_filters(self):
        """Get LOT_SIZE filter from exchange info"""
        try:
            exchange_info = self.client.get_exchange_info()
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == self.config.symbol:
                    for filter_item in symbol_info['filters']:
                        if filter_item['filterType'] == 'LOT_SIZE':
                            self.step_size = float(filter_item['stepSize'])
                            self.min_qty = float(filter_item['minQty'])
                            self.max_qty = float(filter_item['maxQty'])
                            self.logger.log_info(f"LOT_SIZE: min={self.min_qty}, max={self.max_qty}, step={self.step_size}")
                            return
        except Exception as e:
            # Set defaults for common pairs
            if 'BTC' in self.config.symbol:
                self.step_size = 0.00001
                self.min_qty = 0.00001
            elif 'SOL' in self.config.symbol:
                self.step_size = 0.01
                self.min_qty = 0.01
            else:  # ETH and most others
                self.step_size = 0.0001
                self.min_qty = 0.0001
            self.max_qty = 9000.0
            self.logger.log_warning(f"Could not get LOT_SIZE filters, using defaults: {e}")
    
    def _round_quantity(self, quantity: float) -> float:
        """Round quantity to match exchange step size"""
        import math
        precision = int(round(-math.log(self.step_size, 10), 0))
        return round(quantity, precision)
    
    def get_current_price(self) -> float:
        """Get current market price"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.config.symbol)
            return float(ticker['price'])
        except Exception as e:
            self.logger.log_error(f"Price fetch error: {e}")
            return 0.0
    
    def set_triggers(self, reference_price: float):
        """Set ASYMMETRIC triggers based on reference price"""
        self.reference_price = reference_price
        self.buy_trigger = reference_price * 0.99   # -1.0%
        self.sell_trigger = reference_price * 1.015  # +1.5% (ASYMMETRIC!)
        self.logger.log_info(f"Triggers set | Ref: ${reference_price:.2f} | Buy: ${self.buy_trigger:.2f} (-1%) | Sell: ${self.sell_trigger:.2f} (+1.5%)")
    
    def execute_initial_buy(self):
        """Execute initial 50/50 split"""
        current_price = self.get_current_price()
        if current_price <= 0:
            console.print("[red]Cannot get price. Exiting.[/red]")
            exit(1)
        
        # Convert 50% of USDT to crypto
        half_investment = self.config.initial_investment / 2
        crypto_amount = half_investment / current_price
        
        console.print(f"\n[yellow]Executing initial 50/50 split at ${current_price:,.2f}[/yellow]")
        
        if self.config.paper_trading:
            # Paper trading
            self.crypto_balance = crypto_amount
            self.usdt_balance = half_investment
            self.logger.log_trade("INITIAL_BUY", current_price, crypto_amount, half_investment)
        else:
            # Live trading
            try:
                order = self.client.order_market_buy(
                    symbol=self.config.symbol,
                    quoteOrderQty=half_investment
                )
                actual_qty = float(order['executedQty'])
                actual_total = sum(float(fill['price']) * float(fill['qty']) for fill in order['fills'])
                
                self.crypto_balance = actual_qty
                self.usdt_balance = self.config.initial_investment - actual_total
                self.logger.log_trade("INITIAL_BUY", current_price, actual_qty, actual_total)
            except BinanceAPIException as e:
                self.logger.log_error(f"Initial buy failed: {e}")
                console.print(f"[red]Initial buy failed: {e}[/red]")
                exit(1)
        
        # Set both triggers based on current price
        self.set_triggers(current_price)
        
        console.print(f"[green]✓ Initial split complete[/green]")
        console.print(f"[cyan]{self.config.base_asset}:[/cyan] {self.crypto_balance:.6f}")
        console.print(f"[cyan]USDT:[/cyan] ${self.usdt_balance:,.2f}")
    
    def execute_buy(self, current_price: float):
        """Execute a buy order with COMPOUNDING trade size"""
        trade_size = self.get_trade_size(current_price)  # DYNAMIC, not fixed!
        crypto_amount = trade_size / current_price
        crypto_amount = self._round_quantity(crypto_amount)
        
        # Check minimum quantity
        if crypto_amount < self.min_qty:
            self.logger.log_warning(f"Buy amount {crypto_amount} below minimum {self.min_qty}")
            return
        
        if self.config.paper_trading:
            # Paper trading
            if self.usdt_balance >= trade_size:
                self.crypto_balance += crypto_amount
                self.usdt_balance -= trade_size
                self.trade_count += 1
                self.last_buy_price = current_price
                self.logger.log_trade("BUY", current_price, crypto_amount, trade_size)
                
                # Update triggers based on new execution price
                self.set_triggers(current_price)
                
                console.print(f"[green]✓ BUY[/green] {crypto_amount:.6f} {self.config.base_asset} @ ${current_price:,.2f} | Size: ${trade_size:.2f}")
            else:
                self.logger.log_warning(f"Insufficient USDT for buy (need ${trade_size:.2f})")
        else:
            # Live trading
            try:
                order = self.client.order_market_buy(
                    symbol=self.config.symbol,
                    quantity=f"{crypto_amount:.8f}"
                )
                actual_qty = float(order['executedQty'])
                actual_price = float(order['fills'][0]['price'])
                actual_total = sum(float(fill['price']) * float(fill['qty']) for fill in order['fills'])
                
                self.crypto_balance += actual_qty
                self.usdt_balance -= actual_total
                self.trade_count += 1
                self.last_buy_price = actual_price
                self.logger.log_trade("BUY", actual_price, actual_qty, actual_total)
                
                # Update triggers based on new execution price
                self.set_triggers(actual_price)
                
                console.print(f"[green]✓ BUY[/green] {actual_qty:.6f} {self.config.base_asset} @ ${actual_price:,.2f} | Size: ${actual_total:.2f}")
            except BinanceAPIException as e:
                self.logger.log_error(f"Buy order failed: {e}")
    
    def execute_sell(self, current_price: float):
        """Execute a sell order with COMPOUNDING trade size"""
        trade_size = self.get_trade_size(current_price)  # DYNAMIC, not fixed!
        crypto_to_sell = trade_size / current_price
        crypto_to_sell = self._round_quantity(crypto_to_sell)
        
        # Check minimum quantity
        if crypto_to_sell < self.min_qty:
            self.logger.log_warning(f"Sell amount {crypto_to_sell} below minimum {self.min_qty}")
            return
        
        if self.config.paper_trading:
            # Paper trading
            if self.crypto_balance >= crypto_to_sell:
                usdt_received = crypto_to_sell * current_price
                
                # Calculate profit (comparing to trade size)
                profit = usdt_received - trade_size
                
                self.crypto_balance -= crypto_to_sell
                self.usdt_balance += usdt_received
                self.cumulative_profit += profit
                self.trade_count += 1
                self.last_sell_price = current_price
                self.logger.log_trade("SELL", current_price, crypto_to_sell, usdt_received)
                
                # Update triggers based on new execution price
                self.set_triggers(current_price)
                
                profit_color = "green" if profit >= 0 else "red"
                console.print(f"[cyan]✓ SELL[/cyan] {crypto_to_sell:.6f} {self.config.base_asset} @ ${current_price:,.2f} | Size: ${trade_size:.2f} | Profit: [{profit_color}]${profit:+.2f}[/{profit_color}]")
            else:
                self.logger.log_warning(f"Insufficient {self.config.base_asset} for sell (need {crypto_to_sell:.6f})")
        else:
            # Live trading
            try:
                order = self.client.order_market_sell(
                    symbol=self.config.symbol,
                    quantity=f"{crypto_to_sell:.8f}"
                )
                actual_qty = float(order['executedQty'])
                actual_price = float(order['fills'][0]['price'])
                actual_total = sum(float(fill['price']) * float(fill['qty']) for fill in order['fills'])
                profit = actual_total - trade_size
                
                self.crypto_balance -= actual_qty
                self.usdt_balance += actual_total
                self.cumulative_profit += profit
                self.trade_count += 1
                self.last_sell_price = actual_price
                self.logger.log_trade("SELL", actual_price, actual_qty, actual_total)
                
                # Update triggers based on new execution price
                self.set_triggers(actual_price)
                
                profit_color = "green" if profit >= 0 else "red"
                console.print(f"[cyan]✓ SELL[/cyan] {actual_qty:.6f} {self.config.base_asset} @ ${actual_price:,.2f} | Size: ${actual_total:.2f} | Profit: [{profit_color}]${profit:+.2f}[/{profit_color}]")
            except BinanceAPIException as e:
                self.logger.log_error(f"Sell order failed: {e}")
    
    def check_triggers(self, current_price: float):
        """Check BOTH buy and sell triggers simultaneously"""
        # Check sell trigger
        if current_price >= self.sell_trigger:
            # Verify we have enough crypto to sell
            trade_size = self.get_trade_size(current_price)
            crypto_needed = trade_size / current_price
            if self.crypto_balance >= crypto_needed:
                self.execute_sell(current_price)
        
        # Check buy trigger
        if current_price <= self.buy_trigger:
            # Verify we have enough USDT to buy
            trade_size = self.get_trade_size(current_price)
            if self.usdt_balance >= trade_size:
                self.execute_buy(current_price)
    
    def calculate_portfolio_value(self, current_price: float) -> float:
        """Calculate total portfolio value in USDT"""
        return self.usdt_balance + (self.crypto_balance * current_price)
    
    def get_trade_size(self, current_price: float) -> float:
        """
        Calculate DYNAMIC trade size for COMPOUNDING
        Trade size = 5% of CURRENT portfolio (not fixed!)
        This enables exponential growth over time
        """
        portfolio_value = self.calculate_portfolio_value(current_price)
        trade_size = portfolio_value * 0.05
        
        # Log growth if we have a previous trade size
        if self.last_trade_size > 0:
            growth = ((trade_size / self.last_trade_size) - 1) * 100
            growth_vs_initial = ((trade_size / self.initial_trade_size) - 1) * 100
            self.logger.log_info(f"Trade size: ${trade_size:.2f} ({growth:+.2f}% from last, {growth_vs_initial:+.2f}% from initial)")
        else:
            self.logger.log_info(f"Trade size: ${trade_size:.2f} (5% of ${portfolio_value:.2f} portfolio)")
        
        self.last_trade_size = trade_size
        return trade_size
    
    def display_status(self, current_price: float):
        """Display current bot status"""
        console.clear()
        portfolio = self.calculate_portfolio_value(current_price)
        current_trade_size = self.get_trade_size(current_price)
        
        table = Table(title=f"📊 {BOT_NAME} v{BOT_VERSION} - Status", box=box.ROUNDED, border_style="cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        mode = "🧪 PAPER" if self.config.paper_trading else "🔴 LIVE"
        
        table.add_row("Symbol", self.config.symbol)
        table.add_row("Mode", mode)
        table.add_row("Current Price", f"${current_price:,.2f}")
        table.add_row("", "")
        
        # Show BOTH triggers (ASYMMETRIC)
        buy_distance_pct = ((current_price - self.buy_trigger) / self.buy_trigger) * 100
        sell_distance_pct = ((self.sell_trigger - current_price) / current_price) * 100
        
        table.add_row("Reference Price", f"${self.reference_price:,.2f}")
        table.add_row("", "")
        table.add_row("🟢 BUY Trigger (-1.0%)", f"${self.buy_trigger:,.2f} ({buy_distance_pct:+.2f}% away)")
        table.add_row("🔴 SELL Trigger (+1.5%)", f"${self.sell_trigger:,.2f} ({sell_distance_pct:+.2f}% away)")
        
        table.add_row("", "")
        table.add_row(f"{self.config.base_asset} Balance", f"{self.crypto_balance:.6f}")
        table.add_row("USDT Balance", f"${self.usdt_balance:,.2f}")
        table.add_row("Portfolio Value", f"${portfolio:,.2f}")
        table.add_row("", "")
        
        # P&L
        realized_pnl = self.cumulative_profit
        realized_color = "green" if realized_pnl >= 0 else "red"
        unrealized_pnl = portfolio - self.initial_portfolio
        unrealized_color = "green" if unrealized_pnl >= 0 else "red"
        
        table.add_row("Realized P&L", f"[{realized_color}]${realized_pnl:+,.2f}[/{realized_color}]")
        table.add_row("Unrealized P&L", f"[{unrealized_color}]${unrealized_pnl:+,.2f}[/{unrealized_color}]")
        table.add_row("", "")
        
        # Compounding trade size info
        if self.last_trade_size > 0:
            growth_pct = ((current_trade_size / self.initial_trade_size) - 1) * 100
            growth_color = "green" if growth_pct >= 0 else "red"
            table.add_row("Current Trade Size", f"${current_trade_size:.2f}")
            table.add_row("Trade Size Growth", f"[{growth_color}]{growth_pct:+.1f}%[/{growth_color}] from initial")
        else:
            table.add_row("Current Trade Size", f"${current_trade_size:.2f}")
        
        table.add_row("Total Trades", str(self.trade_count))
        
        console.print(table)
        console.print(f"\n[dim]Strategy: ASYMMETRIC GRID (-1% buy / +1.5% sell) with COMPOUNDING (5% of portfolio)[/dim]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
    
    def run(self):
        """Main bot loop"""
        self.logger.log_info("Starting asymmetric grid bot with compounding...")
        
        # Execute initial 50/50 split
        self.execute_initial_buy()
        
        console.print("\n[green]✓ Bot is now running in ASYMMETRIC GRID mode with COMPOUNDING![/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        try:
            consecutive_failures = 0
            while True:
                try:
                    current_price = self.get_current_price()
                    if current_price > 0:
                        # Check BOTH triggers
                        self.check_triggers(current_price)
                        
                        self.display_status(current_price)
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        self.logger.log_warning(f"Price fetch failed ({consecutive_failures}/10)")
                        if consecutive_failures >= 10:
                            self.logger.log_error("Too many failures, pausing for 60s")
                            time.sleep(60)
                            consecutive_failures = 0
                    
                    time.sleep(5)
                    
                except Exception as e:
                    consecutive_failures += 1
                    self.logger.log_error(f"Loop error: {e}")
                    time.sleep(10)
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Bot stopped by user[/yellow]")
            self.logger.log_info("Bot stopped by user")
            final_price = self.get_current_price()
            if final_price > 0:
                self.display_status(final_price)

# === Main Entry Point ===
def main():
    wizard = SetupWizard()
    config = wizard.run()
    
    # Confirmation before starting
    if not config.paper_trading:
        confirm = questionary.confirm(
            "⚠️ You selected LIVE trading. Are you sure?",
            default=False,
            style=custom_style
        ).ask()
        
        if not confirm:
            console.print("[yellow]Cancelled. Switching to paper trading.[/yellow]")
            config.paper_trading = True
    
    bot = DualTriggerBot(config)
    bot.run()

if __name__ == "__main__":
    main()
