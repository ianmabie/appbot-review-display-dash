import os
import logging
from flask import Flask, render_template, jsonify, request
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
    'pool_recycle': 300,  # 5 minutes
    'pool_pre_ping': True,
    'pool_timeout': 10,   # Faster timeout for deployment
    'max_overflow': 0,    # No overflow for single worker
    'pool_size': 1,       # Minimal pool for single worker
    'connect_args': {
        'connect_timeout': 5,  # Faster connection timeout
        'application_name': 'webhook_receiver'
    }
}

# Initialize database
db = SQLAlchemy(app)

# Initialize SocketIO with optimized settings for deployment
socketio = SocketIO(
    app, 
    cors_allowed_origins='*', 
    logger=False,  # Reduce verbose logging in production
    engineio_logger=False,
    ping_timeout=20,  # Faster ping for deployment
    ping_interval=10,
    async_mode='eventlet'
)

# Initialize performance monitoring
from performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor(app)

# Optimize static file serving for deployment
@app.after_request
def add_performance_headers(response):
    """Add performance optimization headers"""
    # Cache static files for 1 hour
    if request.endpoint == 'static':
        response.cache_control.max_age = 3600
        response.cache_control.public = True
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    
    return response

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

# Add the main application routes
@app.route('/')
def index():
    """Display the main page with received reviews (limited to 100 most recent)"""
    from performance_monitor import performance_timer
    
    @performance_timer
    def load_reviews():
        try:
            from models import Review
            # Use more efficient query
            reviews = Review.query.order_by(Review.received_at.desc()).limit(100).all()
            return reviews, False
        except Exception as e:
            app.logger.error(f"Database error: {e}")
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
    import json
    from datetime import datetime
    
    def parse_review(review_data):
        """Parse and validate review data from webhook payload"""
        try:
            from models import Review
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
            app.logger.error(f"Error parsing review data: {e}")
            raise ValueError("Invalid review data format")
    
    try:
        # Log raw request data
        app.logger.info("Received webhook request")
        data = request.get_json()
        
        if data:
            app.logger.info(f"Webhook payload: {json.dumps(data, indent=2)}")
        
        if not data or 'reviews' not in data:
            app.logger.warning("Invalid webhook payload received")
            return jsonify({'error': 'Invalid webhook payload'}), 400

        processed_count = 0
        failed_count = 0
        
        # Process each review in the payload
        for review_data in data['reviews']:
            try:
                review = parse_review(review_data)
                db.session.add(review)
                processed_count += 1
                app.logger.info(f"Processed review from {review.author} (rating: {review.rating})")
            except ValueError as e:
                failed_count += 1
                app.logger.error(f"Skipping invalid review: {e}")
                continue
            except Exception as e:
                failed_count += 1
                app.logger.error(f"Error processing review: {e}")
                continue
        
        if processed_count > 0:
            try:
                # Commit all reviews to database
                db.session.commit()
                app.logger.info(f"Successfully committed {processed_count} reviews to database")
                
                # Keep only the 100 most recent reviews
                from models import Review
                total_reviews = Review.query.count()
                if total_reviews > 100:
                    # Get old reviews to delete (keeping the 100 most recent)
                    old_reviews = Review.query.order_by(Review.received_at.desc()).offset(100).all()
                    for old_review in old_reviews:
                        db.session.delete(old_review)
                    db.session.commit()
                    app.logger.info(f"Cleaned up {len(old_reviews)} old reviews, keeping latest 100")
                
                # Notify clients about new reviews
                socketio.emit('new_reviews', {'count': processed_count})
                
            except Exception as db_error:
                app.logger.error(f"Database commit failed: {db_error}")
                try:
                    db.session.rollback()
                except Exception as rollback_error:
                    app.logger.error(f"Rollback failed: {rollback_error}")
                
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
        app.logger.error("Invalid JSON received in webhook")
        return jsonify({'error': 'Invalid JSON format'}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error processing webhook: {e}")
        try:
            db.session.rollback()
        except Exception as rollback_error:
            app.logger.error(f"Rollback failed: {rollback_error}")
        
        return jsonify({'error': 'Internal server error'}), 500

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
