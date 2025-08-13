import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# Configure logging
app = Flask(__name__)

# Setup Flask secret key (required for sessions and security)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'fallback-secret-key-for-development')

# Configure database - removed connection pooling to reduce overhead
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Removed pool settings to allow connections to close when idle
db = SQLAlchemy(app)
# SocketIO removed to reduce compute costs - using hourly refresh instead

# Database initialization function (called after all models are imported)
def create_tables():
    """Create database tables"""
    try:
        with app.app_context():
            db.create_all()
            app.logger.info("Database tables created successfully")
    except Exception as e:
        app.logger.error(f"Failed to create tables: {e}")

# Custom error handlers
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', 
                         error_code=500,
                         error_message="We're experiencing some technical difficulties. Please try again in a moment."), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html',
                         error_code=404,
                         error_message="The page you're looking for doesn't exist."), 404
