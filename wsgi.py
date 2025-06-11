"""
WSGI entry point for deployment
"""
import os
from app import app, socketio

# Ensure database tables are created
with app.app_context():
    from app import db
    db.create_all()

# For gunicorn deployment
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
else:
    # For WSGI server deployment
    application = app