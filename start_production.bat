@echo off
REM Enhanced EMA Screener Production Startup Script (Windows)
REM =========================================================

echo Starting Enhanced EMA Screener in Production Mode
echo ==================================================

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Set environment variables
set FLASK_ENV=production
set FLASK_DEBUG=False

REM Check if Gunicorn is installed
pip show gunicorn >nul 2>&1
if errorlevel 1 (
    echo Gunicorn not found. Installing...
    pip install gunicorn
)

REM Check dependencies
echo Checking dependencies...
python -c "import sys; required=['flask','pandas','numpy','requests','tqdm']; missing=[p for p in required if not __import__('importlib').util.find_spec(p)]; print('Missing:',missing) if missing else print('All dependencies satisfied'); __import__('subprocess').check_call([sys.executable,'-m','pip','install']+missing) if missing else None"

REM Start the application
echo.
echo Starting Enhanced EMA Screener with Gunicorn...
echo URL: http://localhost:5001
echo Logs: logs/gunicorn_access.log and logs/gunicorn_error.log
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run Gunicorn
gunicorn -c gunicorn_config.py wsgi:application

pause 