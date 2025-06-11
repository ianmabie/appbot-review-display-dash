import os
import logging
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s'
)

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Setup Flask secret key (required for sessions and security)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'fallback-secret-key-for-development')

# Configure database with optimized settings for production
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    app.logger.error("DATABASE_URL environment variable not set")
    raise ValueError("DATABASE_URL is required for application startup")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,  # Slightly less than 5 minutes
    'pool_pre_ping': True,
    'pool_timeout': 30,   # Increased timeout for production
    'max_overflow': 10,   # Allow some overflow connections
    'pool_size': 5,       # Base pool size
    'connect_args': {
        'connect_timeout': 10,
        'application_name': 'webhook_receiver'
    }
}

# Initialize database
db = SQLAlchemy(app)

# Initialize SocketIO with production settings
socketio = SocketIO(
    app, 
    cors_allowed_origins='*', 
    logger=False,  # Reduce verbose logging in production
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

# Health check endpoints for deployment monitoring
@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'webhook_receiver',
        'timestamp': os.environ.get('REPL_ID', 'unknown')
    }), 200

@app.route('/health/ready')
def readiness_check():
    """Readiness check that includes database connectivity"""
    try:
        # Test database connection
        from sqlalchemy import text
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'ready',
            'database': 'connected',
            'service': 'webhook_receiver'
        }), 200
    except Exception as e:
        app.logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not_ready',
            'database': 'disconnected',
            'error': str(e)
        }), 503

# Database initialization function (called after all models are imported)
def create_tables():
    """Create database tables"""
    try:
        with app.app_context():
            db.create_all()
            app.logger.info("Database tables created successfully")
    except Exception as e:
        app.logger.error(f"Failed to create tables: {e}")

# Custom error handlers with improved logging
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    try:
        db.session.rollback()
    except Exception as rollback_error:
        app.logger.error(f"Rollback failed during error handling: {rollback_error}")
    
    return render_template('error.html', 
                         error_code=500,
                         error_message="We're experiencing some technical difficulties. Please try again in a moment."), 500

@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"404 error: {error}")
    return render_template('error.html',
                         error_code=404,
                         error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(503)
def service_unavailable_error(error):
    app.logger.error(f"Service unavailable: {error}")
    return render_template('error.html',
                         error_code=503,
                         error_message="Service temporarily unavailable. Please try again later."), 503
