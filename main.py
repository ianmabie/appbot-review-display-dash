import os
import logging
from datetime import datetime
from flask import request, render_template, jsonify
import json
# SocketIO removed to reduce compute costs

# Configure logging - Set to WARNING to reduce CPU usage
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

from app import app, db
# Import models after app and db are initialized
from models import Review

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
        # Simply query reviews, let SQLAlchemy handle connection efficiently
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
        # Log webhook received (without verbose payload to reduce CPU usage)
        logger.info("Webhook received")
        
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
        
        # Keep only the 100 most recent reviews (optimized bulk delete)
        total_reviews = Review.query.count()
        if total_reviews > 100:
            # Use subquery for efficient bulk delete
            from sqlalchemy import select
            subq = db.session.query(Review.id).order_by(Review.received_at.desc()).limit(100).subquery()
            deleted_count = Review.query.filter(~Review.id.in_(select(subq))).delete(synchronize_session=False)
            db.session.commit()
            logger.info(f"Cleaned up {deleted_count} old reviews, keeping latest 100")
            
        # SocketIO removed - clients will refresh hourly instead
                
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

# Initialize database tables at application startup (simplified without retry loop)
def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            # Import models to ensure they're registered with SQLAlchemy
            from models import Review
            
            # Create all tables
            db.create_all()
            logger.info("Database tables initialized")
            return True
                
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

# Initialize database
init_database()

# Expose Flask app instance for Gunicorn
# This allows Gunicorn to find the app using 'main:app'
application = app

if __name__ == '__main__':
    # Run without SocketIO to reduce compute costs
    app.run(host='0.0.0.0', port=5000, debug=False)