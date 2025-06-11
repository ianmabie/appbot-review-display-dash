import logging
import os
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
        
        # Create a new Review instance
        review = Review()
        
        # Set attributes individually
        if 'app_id' in review_data:
            review.app_id = review_data['app_id']
        if 'app_store_id' in review_data:
            review.app_store_id = review_data['app_store_id']
        review.author = review_data.get('author', 'Unknown')
        review.rating = review_data.get('rating', 0)
        review.subject = review_data.get('subject', 'No subject')
        review.body = review_data.get('body', 'No content')
        review.published_at = published_at
        review.sentiment = review_data.get('sentiment', 'unknown')
        return review
    except Exception as e:
        logger.error(f"Error parsing review data: {e}")
        raise ValueError("Invalid review data format")

@app.route('/')
def index():
    """Display the main page with received reviews"""
    # Get only the 100 most recent reviews
    reviews = Review.query.order_by(Review.received_at.desc()).limit(100).all()
    return render_template('index.html', reviews=reviews)

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
        
        # Commit the new reviews to get their IDs
        db.session.commit()
        
        # Now check and maintain the 100 review limit after processing all reviews
        review_count = Review.query.count()
        if review_count > 100:
            # Get the oldest reviews beyond the 100 limit
            oldest_reviews = Review.query.order_by(Review.received_at.asc()).limit(review_count - 100).all()
            logger.info(f"Removing {len(oldest_reviews)} oldest reviews to maintain 100 review limit")
            
            # Delete the oldest reviews
            for old_review in oldest_reviews:
                db.session.delete(old_review)
            
            # Commit the deletions
            db.session.commit()
            
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

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Check required environment variables only when running directly
    required_vars = ['DATABASE_URL', 'PGDATABASE', 'PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)