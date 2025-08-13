#!/bin/bash
# Enhanced EMA Screener Production Startup Script
# ==============================================

echo "Starting Enhanced EMA Screener in Production Mode"
echo "=================================================="

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False

# Check if Gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Gunicorn not found. Installing..."
    pip install gunicorn
fi

# Check if all required packages are installed
echo "Checking dependencies..."
python -c "
import sys
required_packages = ['flask', 'pandas', 'numpy', 'requests', 'tqdm']
missing = []
for pkg in required_packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f'Missing packages: {missing}')
    print('Installing missing packages...')
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
else:
    print('All dependencies satisfied')
"

# Start the application with Gunicorn
echo "Starting Enhanced EMA Screener with Gunicorn..."
echo "URL: http://localhost:5050"
echo "Logs: logs/gunicorn_access.log and logs/gunicorn_error.log"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run Gunicorn with configuration
gunicorn -c gunicorn_config.py --bind 0.0.0.0:5050 wsgi:application