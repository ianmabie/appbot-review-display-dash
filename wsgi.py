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
    # Import the Flask application instance and SocketIO
    from main import app, socketio, database_ready
    logger.info("Flask application and SocketIO imported successfully")
    
    # For SocketIO applications with eventlet worker, we need to use the SocketIO WSGI app
    # The SocketIO instance wraps the Flask app and provides WebSocket support
    application = socketio
    
    # Validate that the application is properly configured
    if not hasattr(application, 'wsgi_app'):
        logger.error("SocketIO application not properly configured")
        raise RuntimeError("SocketIO WSGI application missing")
    
    logger.info("WSGI application configured successfully")
    logger.info(f"Database ready status: {database_ready}")
    
    # Perform a quick validation
    logger.info("WSGI application validation completed")
    
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

# Additional compatibility layer for different deployment configurations
def get_application():
    """Get the WSGI application instance"""
    return application

if __name__ == "__main__":
    # This won't be called when run with Gunicorn, but useful for testing
    logger.info("Running WSGI application directly (not recommended for production)")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)