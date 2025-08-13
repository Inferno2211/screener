#!/usr/bin/env python3
"""
Enhanced EMA Screener Web Application
====================================

Features:
- 50/100/200 EMA toggles with band filtering
- Customizable band percentage (±2.5% default)
- Dark mode toggle
- Numbered stock rows
- Real-time updates and filtering
- Auto-daily updates after 15:30

Author: Generated for trading analysis
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import logging
from enhanced_ema_screener import EnhancedEMAScreener

app = Flask(__name__)
app.secret_key = 'enhanced_ema_screener_secret_key'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Enhanced EMA Screener
screener = EnhancedEMAScreener()

def check_and_update_data_on_startup():
    """Check for new data and update if needed on app startup"""
    try:
        logger.info("Checking for data updates on startup...")
        
        # Check if we need to update data
        now = datetime.now()
        market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        # Check last update
        last_update_file = screener.cache_dir / "last_update.json"
        last_update_date = None
        
        if last_update_file.exists():
            with open(last_update_file, 'r') as f:
                data = json.load(f)
                last_update_date = datetime.fromisoformat(data['last_update']).date()
        
        # If it's a new day and past market close, trigger update
        if last_update_date is None or (now.date() > last_update_date and now >= market_close_time):
            logger.info("New trading day detected, updating data...")
            success = screener.daily_update_phase()
            if success:
                logger.info("Data updated successfully on startup")
            else:
                logger.info("No update needed or update failed")
        else:
            logger.info("Data is up to date")
            
    except Exception as e:
        logger.error(f"Error checking data on startup: {e}")

# Check for updates on startup (but don't block app initialization)
import threading
def startup_check():
    check_and_update_data_on_startup()

# Run startup check in background thread
startup_thread = threading.Thread(target=startup_check, daemon=True)
startup_thread.start()

@app.route('/')
def index():
    """Main enhanced dashboard page"""
    return render_template('enhanced_index.html')

@app.route('/api/ema-data')
def get_ema_data():
    """API endpoint to get enhanced EMA data"""
    try:
        # Get filter parameters
        ema_filter = request.args.get('ema_filter', 'all')  # all, 50, 100, 200
        band_percentage = float(request.args.get('band_percentage', 2.5))
        
        # Get filtered data
        if ema_filter == 'all':
            df = screener.get_ema_data()
        else:
            df = screener.get_ema_data(ema_filter=ema_filter, band_percentage=band_percentage)
        
        if df.empty:
            return jsonify({
                'status': 'error',
                'message': 'No EMA data available. Please run setup first.',
                'data': []
            })
        
        # Add row numbers
        df = df.reset_index(drop=True)
        df['ROW_NUMBER'] = df.index + 1
        
        # Convert to dict for JSON serialization
        data = df.to_dict('records')
        
        # Calculate summary statistics
        total_stocks = len(df)
        
        # Count stocks above each EMA
        above_ema_50 = 0
        above_ema_100 = 0
        above_ema_200 = 0
        
        if 'LAST_CLOSE' in df.columns:
            if 'EMA_50' in df.columns:
                above_ema_50 = (df['LAST_CLOSE'] > df['EMA_50']).sum()
            if 'EMA_100' in df.columns:
                above_ema_100 = (df['LAST_CLOSE'] > df['EMA_100']).sum()
            if 'EMA_200' in df.columns:
                above_ema_200 = (df['LAST_CLOSE'] > df['EMA_200']).sum()
        
        # Average distances
        avg_distance_50 = df['DISTANCE_FROM_EMA_50'].mean() if 'DISTANCE_FROM_EMA_50' in df.columns else 0
        avg_distance_100 = df['DISTANCE_FROM_EMA_100'].mean() if 'DISTANCE_FROM_EMA_100' in df.columns else 0
        avg_distance_200 = df['DISTANCE_FROM_EMA_200'].mean() if 'DISTANCE_FROM_EMA_200' in df.columns else 0
        
        return jsonify({
            'status': 'success',
            'data': data,
            'summary': {
                'total_stocks': total_stocks,
                'above_ema_50': int(above_ema_50),
                'above_ema_100': int(above_ema_100),
                'above_ema_200': int(above_ema_200),
                'above_ema_50_percentage': round(above_ema_50 / total_stocks * 100, 1) if total_stocks > 0 else 0,
                'above_ema_100_percentage': round(above_ema_100 / total_stocks * 100, 1) if total_stocks > 0 else 0,
                'above_ema_200_percentage': round(above_ema_200 / total_stocks * 100, 1) if total_stocks > 0 else 0,
                'avg_distance_50': round(avg_distance_50, 2),
                'avg_distance_100': round(avg_distance_100, 2),
                'avg_distance_200': round(avg_distance_200, 2),
                'filter_applied': ema_filter,
                'band_percentage': band_percentage,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting EMA data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': []
        })

@app.route('/api/filtered-data')
def get_filtered_data():
    """API endpoint to get filtered and sorted EMA data"""
    try:
        # Get all filter parameters
        ema_filter = request.args.get('ema_filter', 'all')
        band_percentage = float(request.args.get('band_percentage', 2.5))
        sort_by = request.args.get('sort', 'SYMBOL')
        sort_order = request.args.get('order', 'asc')
        search_term = request.args.get('search', '').upper()
        
        # Get base data
        if ema_filter == 'all':
            df = screener.get_ema_data()
        else:
            df = screener.get_ema_data(ema_filter=ema_filter, band_percentage=band_percentage)
        
        if df.empty:
            return jsonify({'status': 'error', 'message': 'No data available', 'data': []})
        
        # Apply search
        if search_term:
            df = df[df['SYMBOL'].str.contains(search_term, na=False)]
        
        # Apply sorting
        if sort_by in df.columns:
            ascending = sort_order == 'asc'
            df = df.sort_values(by=sort_by, ascending=ascending)
        
        # Add row numbers
        df = df.reset_index(drop=True)
        df['ROW_NUMBER'] = df.index + 1
        
        # Convert to dict
        data = df.to_dict('records')
        
        return jsonify({
            'status': 'success',
            'data': data,
            'total_filtered': len(data)
        })
        
    except Exception as e:
        logger.error(f"Error filtering data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': []
        })

@app.route('/api/update-data')
def update_data():
    """API endpoint to trigger daily update"""
    try:
        success = screener.daily_update_phase()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Data updated successfully with latest market data'
            })
        else:
            return jsonify({
                'status': 'info',
                'message': 'No update needed - market not closed or already updated today'
            })
            
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/setup')
def run_setup():
    """API endpoint to run enhanced setup"""
    try:
        success = screener.setup_phase()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Enhanced setup completed successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Setup failed'
            })
            
    except Exception as e:
        logger.error(f"Error running setup: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/status')
def get_status():
    """API endpoint to get enhanced system status"""
    try:
        cache_file = screener.cache_dir / "enhanced_ema_cache.csv"
        last_update_file = screener.cache_dir / "last_update.json"
        
        status = {
            'cache_exists': cache_file.exists(),
            'cache_size': 0,
            'last_update': 'Never',
            'phase': 'Not started',
            'has_enhanced_features': True
        }
        
        if cache_file.exists():
            df = pd.read_csv(cache_file)
            status['cache_size'] = len(df)
            
            # Check if enhanced columns exist
            enhanced_cols = ['EMA_50', 'EMA_100', 'EMA_200', 'WITHIN_BAND_50', 'WITHIN_BAND_100', 'WITHIN_BAND_200']
            status['has_enhanced_features'] = all(col in df.columns for col in enhanced_cols)
        
        if last_update_file.exists():
            with open(last_update_file, 'r') as f:
                update_data = json.load(f)
            status['last_update'] = update_data.get('last_update', 'Unknown')
            status['phase'] = update_data.get('phase', 'Unknown')
        
        return jsonify({
            'status': 'success',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# Create templates directory if it doesn't exist
templates_dir = Path('templates')
templates_dir.mkdir(exist_ok=True)

if __name__ == '__main__':
    print("Enhanced EMA Screener Web Application")
    print("====================================")
    print("Features: 50/100/200 EMAs, Band Filtering, Dark Mode")
    print("Starting Flask server...")
    print("Open http://localhost:5000 in your browser")
    
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Production mode (when run with Gunicorn)
    print("Enhanced EMA Screener - Production Mode")
    print("=======================================") 