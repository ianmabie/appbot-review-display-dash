import logging
from datetime import datetime
from flask import Flask, request, render_template, jsonify
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Store reviews in memory for display purposes
reviews = []

def parse_review(review_data):
    """Parse and validate review data from webhook payload"""
    try:
        return {
            'author': review_data.get('author', 'Unknown'),
            'rating': review_data.get('rating', 0),
            'subject': review_data.get('subject', 'No subject'),
            'body': review_data.get('body', 'No content'),
            'published_at': review_data.get('published_at', 'Unknown date'),
            'sentiment': review_data.get('sentiment', 'unknown'),
            'received_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error parsing review data: {e}")
        raise ValueError("Invalid review data format")

@app.route('/')
def index():
    """Display the main page with received reviews"""
    return render_template('index.html', reviews=reviews)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests"""
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        if not data or 'reviews' not in data:
            return jsonify({'error': 'Invalid webhook payload'}), 400

        # Process each review in the payload
        for review in data['reviews']:
            parsed_review = parse_review(review)
            reviews.insert(0, parsed_review)  # Add to start of list
            
            # Log the received review
            logger.info(f"Received review from {parsed_review['author']}")
            
        return jsonify({'status': 'success', 'message': f"Processed {len(data['reviews'])} reviews"}), 200

    except json.JSONDecodeError:
        logger.error("Invalid JSON received")
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
