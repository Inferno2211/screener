#!/usr/bin/env python3
"""
WSGI Entry Point for Enhanced EMA Screener
==========================================

This file serves as the entry point for Gunicorn to run the
Enhanced EMA Screener web application in production.

Usage:
    gunicorn -c gunicorn_config.py wsgi:application
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import the Flask application
try:
    from enhanced_ema_webapp import app as application
    
    # Set production environment
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    print("Enhanced EMA Screener WSGI application loaded successfully")
    
except ImportError as e:
    print(f"Error importing Enhanced EMA Screener application: {e}")
    raise

if __name__ == "__main__":
    # This allows running the WSGI file directly for testing
    application.run(host='0.0.0.0', port=5000, debug=False) 