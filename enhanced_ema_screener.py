#!/usr/bin/env python3
"""
Enhanced EMA Screener for NSE Markets
====================================

Features:
- 50, 100, 200 day EMAs for all NIFTY Total Market stocks
- Latest market data integration 
- Band filtering (±2.5% customizable)
- Dark mode UI with numbered stocks
- Daily auto-updates after 15:30

Author: Generated for trading analysis
"""

import os
import time
import csv
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from tqdm import tqdm
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class EnhancedEMAScreener:
    def __init__(self):
        # Configuration
        self.nse_main_url = "https://www.nseindia.com/"
        self.historical_api_url = "https://www.nseindia.com/api/historical/cm/equity"
        self.latest_market_url = "https://www.nseindia.com/api/equity-stockIndices?csv=true&index=NIFTY%20TOTAL%20MARKET&selectValFormat=crores"
        self.nifty_csv = "MW-NIFTY-TOTAL-MARKET-13-Aug-2025.csv"
        
        # Directories
        self.data_dir = Path("enhanced_ema_data")
        self.cache_dir = Path("enhanced_ema_cache")
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Files
        self.ema_cache_file = self.cache_dir / "enhanced_ema_cache.csv"
        self.progress_file = self.cache_dir / "download_progress.json"
        self.last_update_file = self.cache_dir / "last_update.json"
        
        # HTTP headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        # Constants
        self.rate_limit_delay = 3
        self.max_retries = 3
        self.session_refresh_interval = 15
        
        # EMA periods
        self.ema_periods = [50, 100, 200]
        
        # Setup logging
        self.setup_logging()
        
        # Session
        self.session = None
        self.request_count = 0
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = f"enhanced_ema_screener_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Enhanced EMA Screener initialized")
        
    def get_session(self):
        """Create a new session with proper headers and cookies"""
        session = requests.Session()
        session.headers.update(self.headers)
        
        try:
            response = session.get(self.nse_main_url, timeout=10)
            self.logger.info("Session created successfully")
            return session
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None
    
    def refresh_session_if_needed(self):
        """Refresh session periodically"""
        if self.session is None or self.request_count >= self.session_refresh_interval:
            self.logger.info("Refreshing session...")
            self.session = self.get_session()
            self.request_count = 0
            time.sleep(2)
    
    def read_nifty_symbols(self):
        """Read all symbols from NIFTY Total Market CSV"""
        try:
            self.logger.info(f"Reading symbols from {self.nifty_csv}")
            df = pd.read_csv(self.nifty_csv)
            
            symbols = []
            for symbol in df['SYMBOL'].tolist():
                if symbol and symbol != 'NIFTY TOTAL MARKET':
                    symbols.append(symbol.strip('"'))
            
            self.logger.info(f"Found {len(symbols)} symbols")
            return symbols
        except Exception as e:
            self.logger.error(f"Error reading symbols: {e}")
            return []
    
    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        prices = np.array(prices, dtype=float)
        alpha = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]
        
        return ema[-1]
    
    def calculate_multiple_emas(self, prices):
        """Calculate 50, 100, 200 day EMAs"""
        emas = {}
        for period in self.ema_periods:
            ema_value = self.calculate_ema(prices, period)
            emas[f'EMA_{period}'] = ema_value
        return emas
    
    def download_stock_data(self, symbol, days=365):
        """Download stock data for given symbol"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        end_str = end_date.strftime("%d-%m-%Y")
        start_str = start_date.strftime("%d-%m-%Y")
        
        params = {
            'symbol': symbol,
            'series': '["EQ"]',
            'from': start_str,
            'to': end_str,
            'csv': 'true'
        }
        
        self.refresh_session_if_needed()
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Downloading {symbol} from {start_str} to {end_str}")
                
                symbol_url = f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
                symbol_response = self.session.get(symbol_url)
                time.sleep(1)
                
                response = self.session.get(self.historical_api_url, params=params)
                self.request_count += 1
                
                if response.status_code == 200:
                    if response.text.strip().startswith("Date,") or "," in response.text:
                        return response.text
                    else:
                        self.logger.warning(f"Non-CSV response for {symbol}: {response.text[:100]}...")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.rate_limit_delay * 2)
                        else:
                            return None
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {symbol}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.rate_limit_delay * 2)
                    else:
                        return None
                        
            except Exception as e:
                self.logger.error(f"Error downloading {symbol}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.rate_limit_delay * 2)
                else:
                    return None
        
        return None
    
    def save_stock_data(self, symbol, csv_data):
        """Save stock data to file"""
        if not csv_data:
            return None
        
        file_path = self.data_dir / f"{symbol}_1yr_data.csv"
        
        try:
            if csv_data.startswith('\ufeff'):
                csv_data = csv_data[1:]
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_data)
            return file_path
        except Exception as e:
            self.logger.error(f"Error saving data for {symbol}: {e}")
            return None
    
    def load_stock_data(self, symbol):
        """Load stock data from file"""
        file_path = self.data_dir / f"{symbol}_1yr_data.csv"
        
        if not file_path.exists():
            return None
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            df.columns = df.columns.str.strip().str.strip('"').str.strip()
            
            if len(df.columns) > 0 and 'ï»¿' in df.columns[0]:
                df.columns = [df.columns[0].replace('ï»¿', '').replace('"', '').strip()] + list(df.columns[1:])
            
            # CRITICAL FIX: Sort data by date to ensure newest data is last
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.sort_values('Date', ascending=True)  # Oldest to newest
                df = df.reset_index(drop=True)
            
            return df
        except Exception as e:
            self.logger.error(f"Error loading data for {symbol}: {e}")
            return None
    
    def calculate_stock_emas(self, symbol):
        """Calculate all EMAs for a stock"""
        df = self.load_stock_data(symbol)
        
        if df is None:
            return None
        
        # Get close prices
        close_prices = []
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['close', 'ltp', 'last', 'price']:
                cleaned_values = df[col].astype(str).str.replace(',', '').str.replace('"', '').str.strip()
                close_prices = pd.to_numeric(cleaned_values, errors='coerce').dropna().tolist()
                if len(close_prices) > 0:
                    break
        
        if len(close_prices) == 0:
            self.logger.error(f"No close price data for {symbol}")
            return None
        
        # Check if we have enough data for largest EMA period
        max_period = max(self.ema_periods)
        if len(close_prices) < max_period:
            self.logger.warning(f"Insufficient data for {symbol}: {len(close_prices)} < {max_period}")
            return None
        
        # Calculate multiple EMAs
        emas = self.calculate_multiple_emas(close_prices)
        emas['LAST_CLOSE'] = close_prices[-1]
        
        return emas
    
    def update_ema_cache(self, symbol, ema_data):
        """Update EMA cache with enhanced data structure"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if self.ema_cache_file.exists():
            try:
                cache_df = pd.read_csv(self.ema_cache_file)
            except:
                cache_df = pd.DataFrame()
        else:
            cache_df = pd.DataFrame()
        
        # Create enhanced record
        record = {
            'SYMBOL': symbol,
            'EMA_50': ema_data.get('EMA_50'),
            'EMA_100': ema_data.get('EMA_100'), 
            'EMA_200': ema_data.get('EMA_200'),
            'LAST_CLOSE': ema_data.get('LAST_CLOSE'),
            'DATE': today
        }
        
        # Calculate band analysis (within ±2.5%)
        if record['LAST_CLOSE'] and record['EMA_50']:
            record['WITHIN_BAND_50'] = abs(record['LAST_CLOSE'] - record['EMA_50']) / record['EMA_50'] <= 0.025
            record['DISTANCE_FROM_EMA_50'] = ((record['LAST_CLOSE'] - record['EMA_50']) / record['EMA_50'] * 100)
        
        if record['LAST_CLOSE'] and record['EMA_100']:
            record['WITHIN_BAND_100'] = abs(record['LAST_CLOSE'] - record['EMA_100']) / record['EMA_100'] <= 0.025
            record['DISTANCE_FROM_EMA_100'] = ((record['LAST_CLOSE'] - record['EMA_100']) / record['EMA_100'] * 100)
            
        if record['LAST_CLOSE'] and record['EMA_200']:
            record['WITHIN_BAND_200'] = abs(record['LAST_CLOSE'] - record['EMA_200']) / record['EMA_200'] <= 0.025
            record['DISTANCE_FROM_EMA_200'] = ((record['LAST_CLOSE'] - record['EMA_200']) / record['EMA_200'] * 100)
        
        # Update or add entry
        mask = cache_df['SYMBOL'] == symbol if 'SYMBOL' in cache_df.columns else pd.Series([False])
        if mask.any():
            for key, value in record.items():
                cache_df.loc[mask, key] = value
        else:
            new_row = pd.DataFrame([record])
            cache_df = pd.concat([cache_df, new_row], ignore_index=True)
        
        # Save cache
        cache_df.to_csv(self.ema_cache_file, index=False)
    
    def fetch_latest_market_data(self):
        """Fetch latest market data from NSE"""
        self.refresh_session_if_needed()
        
        try:
            self.logger.info("Fetching latest market data...")
            response = self.session.get(self.latest_market_url, timeout=15)
            
            if response.status_code == 200 and response.text.strip():
                self.logger.info("Successfully fetched latest market data")
                return response.text
            else:
                self.logger.error(f"Failed to fetch market data: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching latest market data: {e}")
            return None
    
    def parse_latest_market_data(self, csv_data):
        """Parse latest market data and extract stock info"""
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(csv_data))
            
            # Clean column names
            df.columns = df.columns.str.strip().str.strip('"').str.strip()
            
            # Extract relevant columns
            stock_data = {}
            for _, row in df.iterrows():
                symbol = str(row.get('SYMBOL', '')).strip().strip('"')
                if symbol and symbol != 'NIFTY TOTAL MARKET':
                    stock_data[symbol] = {
                        'ltp': row.get('LTP', row.get('CLOSE', 0)),
                        'date': datetime.now().strftime('%d-%m-%Y')
                    }
            
            self.logger.info(f"Parsed {len(stock_data)} stocks from latest market data")
            return stock_data
            
        except Exception as e:
            self.logger.error(f"Error parsing latest market data: {e}")
            return {}
    
    def setup_phase(self):
        """Enhanced setup phase - check existing files first, then download only if needed"""
        self.logger.info("=== STARTING ENHANCED SETUP PHASE ===")
        
        symbols = self.read_nifty_symbols()
        if not symbols:
            self.logger.error("No symbols found!")
            return False
        
        # Check existing files first
        existing_files = {}
        missing_symbols = []
        
        for symbol in symbols:
            file_path = self.data_dir / f"{symbol}_1yr_data.csv"
            if file_path.exists():
                existing_files[symbol] = file_path
                self.logger.info(f"[EXISTS] {symbol} data file found")
            else:
                missing_symbols.append(symbol)
        
        self.logger.info(f"Found {len(existing_files)} existing files, {len(missing_symbols)} files to download")
        
        successful_count = len(existing_files)
        download_count = 0
        ema_count = 0
        
        # Download missing files only
        if missing_symbols:
            with tqdm(total=len(missing_symbols), desc="Downloading missing data") as pbar:
                for symbol in missing_symbols:
                    pbar.set_description(f"Downloading {symbol}")
                    
                    csv_data = self.download_stock_data(symbol)
                    
                    if csv_data:
                        saved_file = self.save_stock_data(symbol, csv_data)
                        if saved_file:
                            download_count += 1
                            self.logger.info(f"[DOWNLOADED] {symbol}")
                        else:
                            self.logger.error(f"[FAIL] Failed to save {symbol}")
                    else:
                        self.logger.error(f"[FAIL] Failed to download {symbol}")
                    
                    pbar.update(1)
                    time.sleep(self.rate_limit_delay)
        
        # Calculate EMAs for all symbols (existing + downloaded)
        all_symbols_with_data = list(existing_files.keys()) + [s for s in missing_symbols if (self.data_dir / f"{s}_1yr_data.csv").exists()]
        
        with tqdm(total=len(all_symbols_with_data), desc="Calculating EMAs") as pbar:
            for symbol in all_symbols_with_data:
                pbar.set_description(f"EMA for {symbol}")
                
                ema_data = self.calculate_stock_emas(symbol)
                if ema_data:
                    self.update_ema_cache(symbol, ema_data)
                    ema_count += 1
                    self.logger.info(f"[OK] {symbol} - EMAs: 50:{ema_data['EMA_50']:.2f}, 100:{ema_data['EMA_100']:.2f}, 200:{ema_data['EMA_200']:.2f}")
                else:
                    self.logger.warning(f"[SKIP] Could not calculate EMAs for {symbol}")
                
                pbar.update(1)
        
        # Save completion status
        with open(self.last_update_file, 'w') as f:
            json.dump({
                'last_update': datetime.now().isoformat(),
                'phase': 'enhanced_setup_complete',
                'total_symbols': len(symbols),
                'existing_files': len(existing_files),
                'downloaded_files': download_count,
                'successful_emas': ema_count
            }, f, indent=2)
        
        self.logger.info(f"=== ENHANCED SETUP COMPLETE ===")
        self.logger.info(f"Existing files: {len(existing_files)}")
        self.logger.info(f"Downloaded: {download_count}")
        self.logger.info(f"Total files: {len(existing_files) + download_count}/{len(symbols)}")
        self.logger.info(f"EMAs calculated: {ema_count}/{len(symbols)}")
        
        return True
    
    def daily_update_phase(self):
        """Enhanced daily update with latest market data"""
        self.logger.info("=== STARTING DAILY UPDATE PHASE ===")
        
        now = datetime.now()
        market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        # Check last update
        last_update_date = None
        if self.last_update_file.exists():
            with open(self.last_update_file, 'r') as f:
                data = json.load(f)
                last_update_date = datetime.fromisoformat(data['last_update']).date()
        
        # Check if update needed
        if now.date() > last_update_date and now >= market_close_time:
            self.logger.info("Market closed for the day, fetching latest data...")
            
            # Fetch latest market data
            latest_data_csv = self.fetch_latest_market_data()
            if not latest_data_csv:
                self.logger.error("Could not fetch latest market data")
                return False
            
            # Parse latest data
            latest_stocks = self.parse_latest_market_data(latest_data_csv)
            if not latest_stocks:
                self.logger.error("Could not parse latest market data")
                return False
            
            # Update each stock's data and recalculate EMAs
            updated_count = 0
            symbols = self.read_nifty_symbols()
            
            with tqdm(total=len(symbols), desc="Updating daily data") as pbar:
                for symbol in symbols:
                    pbar.set_description(f"Updating {symbol}")
                    
                    if symbol in latest_stocks:
                        # Add latest day data to existing file
                        file_path = self.data_dir / f"{symbol}_1yr_data.csv"
                        if file_path.exists():
                            try:
                                df = self.load_stock_data(symbol)
                                if df is not None:
                                    # Add new row for today
                                    new_row = {
                                        'Date': latest_stocks[symbol]['date'],
                                        'close': latest_stocks[symbol]['ltp'],
                                        'ltp': latest_stocks[symbol]['ltp']
                                    }
                                    
                                    # Append new row
                                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                                    df.to_csv(file_path, index=False)
                                    
                                    # Recalculate EMAs
                                    ema_data = self.calculate_stock_emas(symbol)
                                    if ema_data:
                                        self.update_ema_cache(symbol, ema_data)
                                        updated_count += 1
                                        
                            except Exception as e:
                                self.logger.error(f"Error updating {symbol}: {e}")
                    
                    pbar.update(1)
            
            # Update status
            with open(self.last_update_file, 'w') as f:
                json.dump({
                    'last_update': datetime.now().isoformat(),
                    'phase': 'daily_update_complete',
                    'updated_symbols': updated_count
                }, f, indent=2)
            
            self.logger.info(f"Daily update complete. Updated {updated_count} symbols.")
            return True
        else:
            self.logger.info("No update needed - either not a new day or market still open")
            return False
    
    def get_ema_data(self, ema_filter=None, band_percentage=2.5):
        """Get EMA data with filtering options"""
        if not self.ema_cache_file.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(self.ema_cache_file)
            
            # Apply EMA filter
            if ema_filter in ['50', '100', '200']:
                band_col = f'WITHIN_BAND_{ema_filter}'
                if band_col in df.columns:
                    # Recalculate band with custom percentage
                    ema_col = f'EMA_{ema_filter}'
                    if ema_col in df.columns and 'LAST_CLOSE' in df.columns:
                        custom_band = abs(df['LAST_CLOSE'] - df[ema_col]) / df[ema_col] <= (band_percentage / 100)
                        df = df[custom_band]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading EMA cache: {e}")
            return pd.DataFrame()

def main():
    """Main function"""
    screener = EnhancedEMAScreener()
    
    print("Enhanced EMA Screener for NSE Markets")
    print("====================================")
    print("1. Setup Phase - Download all data and calculate 50/100/200 EMAs")
    print("2. Daily Update Phase - Fetch latest market data and update EMAs")
    print("3. Get EMA Data - View current EMA cache")
    
    choice = input("\nSelect option (1/2/3): ").strip()
    
    if choice == '1':
        screener.setup_phase()
    elif choice == '2':
        screener.daily_update_phase()
    elif choice == '3':
        df = screener.get_ema_data()
        print(f"\nEnhanced EMA Data Summary ({len(df)} stocks):")
        if len(df) > 0:
            print(df[['SYMBOL', 'EMA_50', 'EMA_100', 'EMA_200', 'LAST_CLOSE']].head(10))
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main() 