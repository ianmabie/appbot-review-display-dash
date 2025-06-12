#!/usr/bin/env python3
"""
Compatibility layer for main.py WSGI deployment
This ensures that both 'main:app' and 'wsgi:application' entry points work correctly
"""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

try:
    # Import everything from main.py
    from main import app, socketio, database_ready
    
    # Export both Flask app and SocketIO for different deployment configurations
    # This allows Gunicorn to use either:
    # - main:app (traditional Flask)
    # - main:socketio (SocketIO with eventlet)
    # - wsgi:application (recommended)
    
    logger.info("WSGI compatibility layer loaded successfully")
    logger.info(f"Database ready: {database_ready}")
    
except Exception as e:
    logger.error(f"Failed to load WSGI compatibility layer: {e}")
    raise

# Additional exports for maximum compatibility
__all__ = ['app', 'socketio', 'application']

# Alias for wsgi compatibility
application = socketio