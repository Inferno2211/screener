# Enhanced EMA Screener - Production Deployment Guide

## 🚀 Production Deployment with Gunicorn

### Features Added
1. **Auto Data Check on Startup**: Automatically checks for new trading data when app starts
2. **Gunicorn Configuration**: Production-ready WSGI server setup
3. **Background Data Updates**: Non-blocking startup with background data checking

---

## 📦 Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Quick Setup (if not done already)
```bash
python enhanced_quick_setup.py
```

---

## 🌐 Deployment Options

### Option 1: Windows Production (Recommended)
```cmd
start_production.bat
```

### Option 2: Linux/Mac Production
```bash
chmod +x start_production.sh
./start_production.sh
```

### Option 3: Manual Gunicorn
```bash
# Install Gunicorn (if not already installed)
pip install gunicorn

# Create logs directory
mkdir logs

# Start with Gunicorn
gunicorn -c gunicorn_config.py wsgi:application
```

### Option 4: Custom Gunicorn Command
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 30 wsgi:application
```

---

## ⚙️ Configuration

### Gunicorn Settings (`gunicorn_config.py`)
- **Workers**: Auto-calculated based on CPU cores
- **Bind**: `0.0.0.0:5000` (accessible from all interfaces)
- **Timeout**: 30 seconds
- **Logging**: Detailed access and error logs
- **Auto-restart**: Workers restart after 1000 requests

### Environment Variables
```bash
FLASK_ENV=production
FLASK_DEBUG=False
```

---

## 📊 Auto Data Updates

### On Startup Behavior
When the app starts, it automatically:

1. **Checks Last Update Date**: Compares with current date
2. **Market Hours Check**: Verifies if it's past 15:30 IST
3. **Background Update**: Downloads latest market data if needed
4. **Non-blocking**: App starts immediately, updates run in background

### Startup Logs
```
Enhanced EMA Screener - Production Mode
=======================================
Checking for data updates on startup...
New trading day detected, updating data...
Data updated successfully on startup
```

---

## 📁 File Structure

```
enhanced_ema_screener/
├── enhanced_ema_screener.py     # Core EMA engine
├── enhanced_ema_webapp.py       # Flask web application
├── wsgi.py                      # WSGI entry point
├── gunicorn_config.py           # Gunicorn configuration
├── start_production.sh          # Linux/Mac startup script
├── start_production.bat         # Windows startup script
├── requirements.txt             # Python dependencies
├── enhanced_ema_data/           # Stock data storage
├── enhanced_ema_cache/          # EMA cache files
├── logs/                        # Application logs
│   ├── gunicorn_access.log      # Access logs
│   └── gunicorn_error.log       # Error logs
└── templates/
    └── enhanced_index.html      # Web interface
```

---

## 🔍 Monitoring & Logs

### Log Files
- **Access Log**: `logs/gunicorn_access.log` - HTTP requests
- **Error Log**: `logs/gunicorn_error.log` - Application errors
- **App Log**: `enhanced_ema_screener_YYYYMMDD.log` - EMA calculations

### Health Check
```bash
curl http://localhost:5000/api/status
```

### Monitor Workers
```bash
ps aux | grep gunicorn
```

---

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill existing process
   pkill -f gunicorn
   # Or change port in gunicorn_config.py
   ```

2. **Permission Denied (Linux/Mac)**
   ```bash
   chmod +x start_production.sh
   ```

3. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Data Not Updating**
   - Check if it's past 15:30 IST
   - Verify internet connection
   - Check logs for errors

### Performance Tuning

1. **Increase Workers**
   ```python
   # In gunicorn_config.py
   workers = 8  # Adjust based on server capacity
   ```

2. **Adjust Timeout**
   ```python
   # In gunicorn_config.py
   timeout = 60  # For slower data downloads
   ```

---

## 🌐 Deployment Environments

### Development
```bash
python enhanced_ema_webapp.py
```

### Production (Local)
```bash
./start_production.sh
# or
start_production.bat
```

### Production (Server)
```bash
# With daemon mode
gunicorn -c gunicorn_config.py -D wsgi:application

# Check status
ps aux | grep gunicorn
```

### Docker (Optional)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-c", "gunicorn_config.py", "wsgi:application"]
```

---

## ✅ Features

### Auto Data Management
- ✅ Startup data checking
- ✅ Background updates
- ✅ Date-based update logic
- ✅ Market hours awareness

### Production Ready
- ✅ Gunicorn WSGI server
- ✅ Worker process management
- ✅ Comprehensive logging
- ✅ Error handling
- ✅ Auto-restart capabilities

### Monitoring
- ✅ Health check endpoint
- ✅ Detailed access logs
- ✅ Application metrics
- ✅ Process monitoring

---

## 📞 Support

For deployment issues:
1. Check logs in `logs/` directory
2. Verify all dependencies are installed
3. Ensure network connectivity for NSE data
4. Check system resources (CPU, Memory)

**Your Enhanced EMA Screener is now production-ready! 🎯** 