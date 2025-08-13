# Gunicorn Configuration for Enhanced EMA Screener
# =================================================

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "enhanced_ema_screener"

# Daemon mode (set to True for background running)
daemon = False

# User/group to run as (uncomment and modify as needed)
# user = "www-data"
# group = "www-data"

# Directory to run the app from
chdir = os.path.dirname(os.path.abspath(__file__))

# Preload the application for better performance
preload_app = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Enhanced EMA Screener server is ready. Workers: %s", server.cfg.workers)

def worker_exit(server, worker):
    """Called when a worker is exited."""
    server.log.info("Worker %s exited", worker.pid)

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Enhanced EMA Screener server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Enhanced EMA Screener server...")

# Environment variables
raw_env = [
    'FLASK_ENV=production',
    'PYTHONPATH=/path/to/your/app'
] 