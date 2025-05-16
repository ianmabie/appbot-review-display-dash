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
    """Display the main page with received reviews"""
    reviews = Review.query.order_by(Review.received_at.desc()).all()
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
                
                # Check and maintain 100 review limit
                review_count = Review.query.count()
                if review_count > 100:
                    # Delete oldest reviews beyond the 100 limit
                    oldest_reviews = Review.query.order_by(Review.received_at.asc()).limit(review_count - 100).all()
                    for old_review in oldest_reviews:
                        db.session.delete(old_review)
                        
            except ValueError as e:
                logger.error(f"Skipping invalid review: {e}")
                continue
        
        # Commit all changes to database
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)