"""Gunicorn configuration for production deployment"""

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes - optimized for Replit deployment
workers = 1  # Single worker for Replit's resource constraints
worker_class = "eventlet"  # Required for SocketIO
worker_connections = 100  # Reduced for single worker
timeout = 60  # Shorter timeout for faster failure detection
keepalive = 5  # Increased keepalive for better connection reuse

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "webhook_receiver"

# Application - WSGI entry point
# Note: This is configured in the deployment command, not here
# But we keep this for reference: wsgi:application

# Ensure proper SocketIO configuration
def post_fork(server, worker):
    """Called after a worker is forked"""
    server.log.info(f"Worker {worker.pid} ready to serve SocketIO requests")

def worker_abort(worker):
    """Called when a worker is killed by SIGABRT"""
    worker.log.info(f"Worker {worker.pid} aborted")

# Preload the application for better performance
preload_app = True

# Enable graceful timeout handling
graceful_timeout = 30

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Enable proper error handling
capture_output = True

def when_ready(server):
    """Called when the server is ready to serve requests"""
    server.log.info("Webhook receiver server is ready to accept connections")

def on_starting(server):
    """Called before the master process is initialized"""
    server.log.info("Starting webhook receiver application")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP"""
    server.log.info("Reloading webhook receiver application")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal"""
    worker.log.info("Worker received interrupt signal")