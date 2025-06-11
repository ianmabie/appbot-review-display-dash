#!/usr/bin/env python3
"""
WSGI entry point for Gunicorn deployment.
This file provides the application instance that Gunicorn will use.
"""

import os
import sys
import logging

# Configure logging for production deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting WSGI application...")

try:
    # Import the Flask application instance
    from main import app
    logger.info("Flask application imported successfully")
    
    # Import SocketIO for WebSocket support
    from main import socketio
    logger.info("SocketIO imported successfully")
    
    # The WSGI application that Gunicorn will serve
    # For SocketIO applications, we need to use the SocketIO WSGI app
    application = socketio
    
    logger.info("WSGI application configured successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize WSGI application: {e}")
    raise

# Health check for WSGI
def wsgi_health_check():
    """Quick health check for WSGI startup"""
    try:
        with app.app_context():
            return True
    except Exception as e:
        logger.error(f"WSGI health check failed: {e}")
        return False

if __name__ == "__main__":
    # This won't be called when run with Gunicorn, but useful for testing
    logger.info("Running WSGI application directly (not recommended for production)")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)