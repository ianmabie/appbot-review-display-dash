import os
import logging
import sys
from datetime import datetime
from flask import request, render_template, jsonify
import json
from flask_socketio import SocketIO

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log startup process
logger.info("Starting application initialization...")

try:
    from app import app, db
    logger.info("Flask app and database imported successfully")
    
    # Import models after app and db are initialized
    from models import Review
    logger.info("Models imported successfully")
    
    # SocketIO is already initialized in app.py
    from app import socketio
    logger.info("SocketIO imported successfully")
    
except Exception as e:
    logger.error(f"Failed to import application components: {e}")
    raise

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
    from performance_monitor import performance_timer
    
    @performance_timer
    def load_reviews():
        if not database_ready:
            return [], True
        
        try:
            # Use more efficient query
            reviews = Review.query.order_by(Review.received_at.desc()).limit(100).all()
            return reviews, False
        except Exception as e:
            logger.error(f"Database error: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return [], True
    
    reviews, database_error = load_reviews()
    
    response = app.make_response(render_template('index.html', reviews=reviews, database_error=database_error))
    
    # Add caching headers for better performance
    response.cache_control.max_age = 30  # Cache for 30 seconds
    response.cache_control.public = True
    
    return response

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests"""
    try:
        # Log raw request data
        logger.info("Received webhook request")
        data = request.get_json()
        
        if data:
            logger.info(f"Webhook payload: {json.dumps(data, indent=2)}")
        
        if not data or 'reviews' not in data:
            logger.warning("Invalid webhook payload received")
            return jsonify({'error': 'Invalid webhook payload'}), 400

        # Check if database is available for processing
        if not database_ready:
            logger.warning("Database not ready - webhook processing skipped")
            return jsonify({
                'status': 'warning',
                'message': 'Database not available - reviews not processed'
            }), 503

        processed_count = 0
        failed_count = 0
        
        # Process each review in the payload
        for review_data in data['reviews']:
            try:
                review = parse_review(review_data)
                db.session.add(review)
                processed_count += 1
                logger.info(f"Processed review from {review.author} (rating: {review.rating})")
            except ValueError as e:
                failed_count += 1
                logger.error(f"Skipping invalid review: {e}")
                continue
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing review: {e}")
                continue
        
        if processed_count > 0:
            try:
                # Commit all reviews to database
                db.session.commit()
                logger.info(f"Successfully committed {processed_count} reviews to database")
                
                # Keep only the 100 most recent reviews
                total_reviews = Review.query.count()
                if total_reviews > 100:
                    # Get old reviews to delete (keeping the 100 most recent)
                    old_reviews = Review.query.order_by(Review.received_at.desc()).offset(100).all()
                    for old_review in old_reviews:
                        db.session.delete(old_review)
                    db.session.commit()
                    logger.info(f"Cleaned up {len(old_reviews)} old reviews, keeping latest 100")
                
                # Notify clients about new reviews
                socketio.emit('new_reviews', {'count': processed_count})
                
            except Exception as db_error:
                logger.error(f"Database commit failed: {db_error}")
                try:
                    db.session.rollback()
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
                
                return jsonify({
                    'status': 'error',
                    'message': 'Database error during processing'
                }), 500
                
        return jsonify({
            'status': 'success',
            'message': f"Processed {processed_count} reviews successfully",
            'processed': processed_count,
            'failed': failed_count
        }), 200

    except json.JSONDecodeError:
        logger.error("Invalid JSON received in webhook")
        return jsonify({'error': 'Invalid JSON format'}), 400
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"Rollback failed: {rollback_error}")
        
        return jsonify({'error': 'Internal server error'}), 500

# Database initialization with improved error handling
def init_database():
    """Initialize database tables with optimized error handling for deployment"""
    import time
    start_time = time.time()
    logger.info("Starting database initialization...")
    
    # Check if DATABASE_URL is available
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not found")
        return False
    
    logger.info("Database URL found")
    
    max_retries = 3  # Reduced retries for faster deployment
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                logger.info(f"Database attempt {retry_count + 1}/{max_retries}")
                
                # Import models
                from models import Review
                
                # Quick connection test
                from sqlalchemy import text
                connection = db.engine.connect()
                try:
                    connection.execute(text('SELECT 1'))
                    logger.info("Database connection verified")
                finally:
                    connection.close()
                
                # Create tables
                db.create_all()
                
                # Quick verification
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                
                if 'reviews' in tables:
                    elapsed = time.time() - start_time
                    logger.info(f"Database ready in {elapsed:.2f}s")
                    return True
                else:
                    logger.warning("Reviews table missing after creation")
                    return False
                
        except Exception as e:
            retry_count += 1
            logger.error(f"Database attempt {retry_count} failed: {str(e)}")
            
            if retry_count >= max_retries:
                logger.error("Database initialization failed - continuing with limited functionality")
                return False
                
            # Shorter wait for deployment
            time.sleep(1)
    
    return False

# Initialize database with startup logging
logger.info("Initializing database...")
database_ready = init_database()

if database_ready:
    logger.info("Database initialization successful - application ready")
else:
    logger.warning("Database initialization failed - application running in degraded mode")

# For Gunicorn deployment, expose the app instance
# Gunicorn will look for 'main:app'
logger.info("Application setup complete - ready for deployment")

if __name__ == '__main__':
    logger.info("Starting application in development mode...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)