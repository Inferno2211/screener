# EMA Screener for NSE Markets

A comprehensive 200-day Exponential Moving Average (EMA) screening system for all stocks in the NIFTY Total Market.

## Features

- **Complete Market Coverage**: Screens 750+ stocks from NSE Total Market
- **Real-time EMA Calculation**: 200-day EMA with live updates
- **Beautiful Web Interface**: Modern, responsive dashboard with filtering and sorting
- **Intelligent Caching**: Two-stage caching system for optimal performance
- **Daily Auto-updates**: Automatic data refresh after market hours (post 15:30)
- **Progress Tracking**: Comprehensive logging and progress indicators
- **Robust Data Handling**: Error handling and retry mechanisms

## System Architecture

### Two-Stage Process

1. **Setup Phase**: Download 1-year OHLC data for all stocks and calculate initial EMAs
2. **Daily Update Phase**: Incremental updates with new trading data

### File Structure

```
ema_screener/
├── ema_screener.py          # Main EMA calculation engine
├── ema_webapp.py            # Flask web application
├── templates/
│   └── index.html           # Web dashboard
├── ema_data/               # Stock data storage
├── ema_cache/              # EMA cache and progress files
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. **Clone or download the files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Step 1: Initial Setup (First Run)

Run the EMA screener setup to download all stock data:

```bash
python ema_screener.py
```

Select option `1` for "Setup Phase". This will:
- Read all 750+ stock symbols from MW-NIFTY-TOTAL-MARKET.csv
- Download 1 year of OHLC data for each stock
- Calculate 200-day EMA for each stock
- Save everything to cache files

**Expected time**: 30-60 minutes (depending on network speed)

### Step 2: Launch Web Application

```bash
python ema_webapp.py
```

Open your browser and go to: `http://localhost:5000`

### Daily Updates

The system automatically checks for updates when you:
- Click "Update Data" in the web interface
- Run option `2` in the command-line interface
- The web app will auto-check after 15:30 each trading day

## Web Dashboard Features

### Summary Statistics
- Total stocks tracked
- Stocks above/below 200-EMA
- Percentage breakdown
- Average distance from EMA

### Filtering & Sorting
- **Filter**: All stocks, Above EMA, Below EMA
- **Sort by**: Symbol, EMA value, Distance from EMA, Last close
- **Search**: Find specific stocks by symbol
- **Auto-refresh**: Real-time updates every 30 seconds

### Data Display
- Stock symbol and last close price
- 200-EMA value
- Position (Above/Below EMA)
- Percentage distance from EMA
- Last update date

## Configuration

### Timing
- **Market close check**: 15:30 IST
- **Auto-refresh interval**: 30 seconds
- **Rate limiting**: 3 seconds between API calls
- **Session refresh**: Every 15 requests

### Data Storage
- **Stock data**: `ema_data/` directory (CSV files)
- **EMA cache**: `ema_cache/ema_200_cache.csv`
- **Progress tracking**: `ema_cache/download_progress.json`
- **Last update**: `ema_cache/last_update.json`

## Logging

Comprehensive logging is available:
- **Console output**: Real-time progress and status
- **Log files**: `ema_screener_YYYYMMDD.log`
- **Progress bars**: Visual progress indicators
- **Success/failure tracking**: Detailed status for each stock

## API Endpoints

The web application provides REST API endpoints:

- `GET /api/ema-data` - Get all EMA data with summary
- `GET /api/filtered-data` - Get filtered and sorted data
- `GET /api/update-data` - Trigger data update
- `GET /api/status` - Get system status

## Troubleshooting

### Common Issues

1. **"No EMA data available"**
   - Run the setup phase first (`python ema_screener.py` → option 1)

2. **Download failures**
   - The system has retry mechanisms built-in
   - Check your internet connection
   - NSE servers may be temporarily unavailable

3. **Insufficient data for EMA**
   - Some stocks may not have 200 days of data
   - These will be logged as warnings but won't stop the process

4. **Web app not loading**
   - Ensure Flask is installed: `pip install flask`
   - Check if port 5000 is available
   - Look for error messages in the console

### Performance Tips

1. **First setup**: Be patient, downloading 750+ stocks takes time
2. **Daily updates**: Much faster as they only fetch recent data
3. **Memory usage**: Large datasets may require 2-4GB RAM
4. **Storage**: Expect 200-500MB for all stock data

## Data Sources

- **Stock List**: MW-NIFTY-TOTAL-MARKET-13-Aug-2025.csv
- **Price Data**: NSE Historical Data API
- **Update Frequency**: Daily after market close

## Technical Details

### EMA Calculation
- **Formula**: EMA = α × Current Price + (1-α) × Previous EMA
- **α (smoothing factor)**: 2 / (period + 1) = 2 / 201 ≈ 0.00995
- **Period**: 200 days
- **Minimum data**: 200 trading days required

### Caching Strategy
- **Level 1**: Raw stock data files (1 year OHLC)
- **Level 2**: Calculated EMA cache with metadata
- **Incremental updates**: Only fetch latest data, recalculate EMA

## License

Created for trading analysis and educational purposes.

## Support

For issues or questions:
1. Check the log files for detailed error messages
2. Ensure all dependencies are installed
3. Verify your internet connection for NSE data access

---

**Disclaimer**: This tool is for educational and analysis purposes only. Always do your own research before making trading decisions. 