import os
import time
import csv
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nse_download.log"),
        logging.StreamHandler()
    ]
)

# Constants
NSE_MAIN_URL = "https://www.nseindia.com/"
HISTORICAL_API_URL = "https://www.nseindia.com/api/historical/cm/equity"
OUTPUT_DIR = "stock_data"
COMPANIES_FILE = "ind_nifty100list.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0"
}
RATE_LIMIT_DELAY = 5  # seconds between requests
MAX_RETRIES = 3
SESSION_REFRESH_INTERVAL = 10  # refresh session after every 10 requests

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_companies():
    """Read company symbols from CSV file"""
    try:
        df = pd.read_csv(COMPANIES_FILE)
        # Check if the expected columns are present
        if 'Symbol' in df.columns:
            companies = df['Symbol'].tolist()
            logging.info(f"Successfully loaded {len(companies)} companies")
            return companies
        else:
            # Try to find the column containing symbols
            for col in df.columns:
                if any(s in col.lower() for s in ['symbol', 'ticker']):
                    companies = df[col].tolist()
                    logging.info(f"Using column '{col}' for symbols. Loaded {len(companies)} companies")
                    return companies
            
            logging.error(f"Could not find Symbol column in {COMPANIES_FILE}. Available columns: {df.columns.tolist()}")
            return []
    except Exception as e:
        logging.error(f"Error reading companies file: {e}")
        return []

def generate_date_ranges(years=15):
    """Generate date ranges for the past 15 years, in 1-year chunks"""
    end_date = datetime.now()
    date_ranges = []
    
    for i in range(years):
        end = end_date - timedelta(days=365 * i)
        start = end - timedelta(days=365)
        
        # Format dates as DD-MM-YYYY
        end_str = end.strftime("%d-%m-%Y")
        start_str = start.strftime("%d-%m-%Y")
        
        date_ranges.append((start_str, end_str))
    
    return date_ranges

def get_session():
    """Create a new session with proper cookies for NSE website"""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Visit the main NSE website to get necessary cookies
    try:
        logging.info("Initializing new NSE session...")
        response = session.get(NSE_MAIN_URL)
        if response.status_code == 200:
            logging.info("Session initialized successfully")
            return session
        else:
            logging.error(f"Failed to initialize session: HTTP {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error initializing session: {e}")
        return None

def download_data(session, symbol, start_date, end_date, retry_count=0):
    """Download data for a given symbol and date range using the provided session"""
    params = {
        'symbol': symbol,
        'series': '["EQ"]',
        'from': start_date,
        'to': end_date,
        'csv': 'true'
    }
    
    try:
        logging.debug(f"Downloading {symbol} from {start_date} to {end_date}")

        # First try to access the symbol directly to trigger cookie updates
        symbol_url = f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
        symbol_response = session.get(symbol_url)
        time.sleep(1)  # Small delay after accessing the symbol page
        
        # Now download the CSV data
        response = session.get(HISTORICAL_API_URL, params=params)
        
        if response.status_code == 200:
            # Check if response is CSV data
            if response.text.strip().startswith("Date,") or "," in response.text:
                return response.text
            else:
                logging.warning(f"Received non-CSV response for {symbol}: {response.text[:100]}...")
                if retry_count < MAX_RETRIES:
                    logging.info(f"Retrying {symbol} ({retry_count+1}/{MAX_RETRIES})...")
                    time.sleep(RATE_LIMIT_DELAY * 2)  # Extra delay before retry
                    
                    if retry_count == MAX_RETRIES - 1:
                        # On last retry, get a fresh session
                        session = get_session()
                    
                    return download_data(session, symbol, start_date, end_date, retry_count + 1)
                else:
                    logging.error(f"Max retries reached for {symbol}")
                    return None
        else:
            logging.warning(f"Failed to download {symbol}: HTTP {response.status_code}")
            if retry_count < MAX_RETRIES:
                logging.info(f"Retrying {symbol} ({retry_count+1}/{MAX_RETRIES})...")
                time.sleep(RATE_LIMIT_DELAY * 2)  # Extra delay before retry
                
                if retry_count == MAX_RETRIES - 1:
                    # On last retry, get a fresh session
                    session = get_session()
                
                return download_data(session, symbol, start_date, end_date, retry_count + 1)
            else:
                logging.error(f"Max retries reached for {symbol}")
                return None
    except Exception as e:
        logging.error(f"Error downloading {symbol}: {e}")
        if retry_count < MAX_RETRIES:
            logging.info(f"Retrying {symbol} ({retry_count+1}/{MAX_RETRIES})...")
            time.sleep(RATE_LIMIT_DELAY * 2)
            
            if retry_count == MAX_RETRIES - 1:
                # On last retry, get a fresh session
                session = get_session()
            
            return download_data(session, symbol, start_date, end_date, retry_count + 1)
        return None

def save_temp_data(symbol, date_range, data):
    """Save temporary data file"""
    if not data:
        return None
    
    start_date, end_date = date_range
    filename = os.path.join(OUTPUT_DIR, f"{symbol}_{start_date}_{end_date}.csv")
    
    try:
        with open(filename, 'w', newline='') as f:
            f.write(data)
        return filename
    except Exception as e:
        logging.error(f"Error saving temporary file for {symbol}: {e}")
        return None

def merge_files(symbol, temp_files):
    """Merge all temporary files for a symbol into one CSV"""
    if not temp_files:
        logging.warning(f"No data files to merge for {symbol}")
        return
    
    all_data = []
    header = None
    
    # Read all temporary files
    for file in temp_files:
        if file and os.path.exists(file):
            try:
                df = pd.read_csv(file)
                all_data.append(df)
            except Exception as e:
                logging.error(f"Error reading {file}: {e}")
    
    if not all_data:
        logging.warning(f"No valid data found for {symbol}")
        return
    
    # Concatenate all dataframes
    try:
        merged_data = pd.concat(all_data, ignore_index=True)
        # Remove duplicates if any
        merged_data = merged_data.drop_duplicates()
        # Sort by date
        if 'Date' in merged_data.columns:
            merged_data['Date'] = pd.to_datetime(merged_data['Date'])
            merged_data = merged_data.sort_values('Date')
        
        # Save merged file
        output_file = os.path.join(OUTPUT_DIR, f"{symbol}_15yr_data.csv")
        merged_data.to_csv(output_file, index=False)
        logging.info(f"Successfully created merged file for {symbol}: {output_file}")
        
        # Clean up temporary files
        for file in temp_files:
            if file and os.path.exists(file):
                os.remove(file)
    except Exception as e:
        logging.error(f"Error merging data for {symbol}: {e}")

def main():
    companies = read_companies()
    companies = companies[50:];
    # print(companies)
    date_ranges = generate_date_ranges()
    
    if not companies:
        logging.error("No companies loaded. Exiting.")
        return
    
    logging.info(f"Starting download for {len(companies)} companies over {len(date_ranges)} time periods")
    
    # Start with a fresh session
    session = get_session()
    if not session:
        logging.error("Failed to initialize session. Exiting.")
        return
    
    # Track requests to refresh session periodically
    request_count = 0
    
    # Process each company
    for company_idx, symbol in enumerate(tqdm(companies, desc="Processing companies")):
        logging.info(f"Processing {symbol} ({company_idx+1}/{len(companies)})")
        temp_files = []
        
        # Download data for each date range
        for range_idx, date_range in enumerate(tqdm(date_ranges, desc=f"Downloading {symbol}", leave=False)):
            # Check if we need to refresh the session
            request_count += 1
            if request_count % SESSION_REFRESH_INTERVAL == 0:
                logging.info("Refreshing session...")
                session = get_session()
                if not session:
                    session = get_session()  # Try one more time
                    if not session:
                        logging.error("Failed to refresh session. Continuing with existing session.")
                        session = requests.Session()
                        session.headers.update(HEADERS)
                time.sleep(RATE_LIMIT_DELAY)  # Wait after refreshing session
            
            start_date, end_date = date_range
            data = download_data(session, symbol, start_date, end_date)
            
            if data:
                temp_file = save_temp_data(symbol, date_range, data)
                if temp_file:
                    temp_files.append(temp_file)
                    logging.info(f"Saved data for {symbol} ({start_date} to {end_date})")
            else:
                logging.warning(f"No data for {symbol} ({start_date} to {end_date})")
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
        
        # Merge all files for this company
        merge_files(symbol, temp_files)
        
        # Additional delay between companies
        time.sleep(2)
    
    logging.info("Download process completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")