import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Configure logging
app = Flask(__name__)

# Configure secret key - use a more robust fallback for production
secret_key = os.environ.get('FLASK_SECRET_KEY')
if not secret_key:
    # Generate a random secret key if none is provided
    import secrets
    secret_key = secrets.token_hex(32)
    print("WARNING: Using auto-generated secret key. Set FLASK_SECRET_KEY environment variable for production.")

app.config['SECRET_KEY'] = secret_key

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins='*', logger=True, engineio_logger=True)
