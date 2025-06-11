import os
import logging
from datetime import datetime
from flask import request, render_template, jsonify
import json
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from app import app, db
# Import models after app and db are initialized
from models import Review

# SocketIO is already initialized in app.py
from app import socketio

def parse_review(review_data):
    """Parse and validate review data from webhook payload"""
    try:
        published_at = datetime.strptime(review_data.get('published_at', ''), '%Y-%m-%d').date() if review_data.get('published_at') else None
        
        return Review(
            app_id=review_data.get('app_id'),
            app_store_id=review_data.get('app_store_id'),
            author=review_data.get('author', 'Unknown'),
            rating=review_data.get('rating', 0),
            subject=review_data.get('subject', 'No subject'),
            body=review_data.get('body', 'No content'),
            published_at=published_at,
            sentiment=review_data.get('sentiment', 'unknown')
        )
    except Exception as e:
        logger.error(f"Error parsing review data: {e}")
        raise ValueError("Invalid review data format")

@app.route('/')
def index():
    """Display the main page with received reviews (limited to 100 most recent)"""
    try:
        # Check if database tables exist
        if not db.engine.dialect.has_table(db.engine.connect(), 'reviews'):
            logger.warning("Reviews table not found, initializing database")
            db.create_all()
            reviews = []
        else:
            reviews = Review.query.order_by(Review.received_at.desc()).limit(100).all()
        
        return render_template('index.html', reviews=reviews)
    except Exception as e:
        logger.error(f"Database error in index route: {e}")
        try:
            db.session.rollback()
        except:
            pass  # Ignore rollback errors
        
        # Return a safe fallback page
        return render_template('index.html', reviews=[]), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests"""
    try:
        # Log raw request data
        logger.info("Received webhook payload:")
        logger.info(json.dumps(request.get_json(), indent=2))
        
        # Get the JSON data from the request
        data = request.get_json()
        
        if not data or 'reviews' not in data:
            return jsonify({'error': 'Invalid webhook payload'}), 400

        # Process each review in the payload
        processed_count = 0
        for review_data in data['reviews']:
            try:
                review = parse_review(review_data)
                db.session.add(review)
                processed_count += 1
                logger.info(f"Received review from {review.author}")
            except ValueError as e:
                logger.error(f"Skipping invalid review: {e}")
                continue
        
        # Commit all reviews to database
        db.session.commit()
        
        # Keep only the 100 most recent reviews
        total_reviews = Review.query.count()
        if total_reviews > 100:
            # Get IDs of reviews to delete (keeping the 100 most recent)
            old_reviews = Review.query.order_by(Review.received_at.desc()).offset(100).all()
            for old_review in old_reviews:
                db.session.delete(old_review)
            db.session.commit()
            logger.info(f"Cleaned up {len(old_reviews)} old reviews, keeping latest 100")
            
        # Notify clients about new reviews
        socketio.emit('new_reviews', {'count': processed_count})
                
        return jsonify({
            'status': 'success',
            'message': f"Processed {processed_count} reviews"
        }), 200

    except json.JSONDecodeError:
        logger.error("Invalid JSON received")
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# Initialize database tables at application startup
def init_database():
    """Initialize database tables and handle connection issues"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                # Import models to ensure they're registered with SQLAlchemy
                from models import Review
                
                # Test database connection first
                from sqlalchemy import text
                with db.engine.connect() as connection:
                    connection.execute(text('SELECT 1'))
                
                # Create all tables
                db.create_all()
                logger.info("Database tables initialized successfully")
                return True
                
        except Exception as e:
            retry_count += 1
            logger.error(f"Database initialization attempt {retry_count} failed: {e}")
            if retry_count >= max_retries:
                logger.error("Failed to initialize database after maximum retries")
                return False
            import time
            time.sleep(2)  # Wait before retry
    
    return False

# Initialize database
if not init_database():
    logger.error("Database initialization failed - application may not work properly")

# Expose Flask app instance for Gunicorn
# This allows Gunicorn to find the app using 'main:app'
application = app

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)