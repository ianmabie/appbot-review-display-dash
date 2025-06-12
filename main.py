#!/usr/bin/env python3
"""
Main application entry point for development and deployment compatibility.
This file provides multiple entry points for different deployment configurations.
"""

import os
import logging
import sys

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("Starting main application entry point...")

try:
    # Import the Flask application and SocketIO
    from app import app, db, socketio
    logger.info("Flask application and SocketIO imported successfully")
    
    # Import models to ensure they're registered
    from models import Review
    logger.info("Models imported successfully")
    
    # Initialize database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables initialized")
    
    logger.info("Application ready for deployment")
    
except Exception as e:
    logger.error(f"Failed to initialize application: {e}")
    raise

# Export multiple entry points for deployment compatibility
__all__ = ['app', 'socketio', 'application']

# Primary application instance for SocketIO deployments
application = socketio

# Database ready flag for compatibility
database_ready = True

# Development server entry point
if __name__ == '__main__':
    logger.info("Starting development server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)