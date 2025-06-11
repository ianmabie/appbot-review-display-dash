from datetime import datetime
from pytz import timezone
from app import db

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer)
    app_store_id = db.Column(db.String(50))
    author = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(200))
    body = db.Column(db.Text)
    published_at = db.Column(db.Date)
    sentiment = db.Column(db.String(50))
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, app_id=None, app_store_id=None, author=None, rating=None, 
                 subject=None, body=None, published_at=None, sentiment=None):
        self.app_id = app_id
        self.app_store_id = app_store_id
        self.author = author
        self.rating = rating
        self.subject = subject
        self.body = body
        self.published_at = published_at
        self.sentiment = sentiment

    def to_dict(self):
        # Convert UTC to EST
        est_time = self.received_at.astimezone(timezone('America/New_York'))
        return {
            'id': self.id,
            'author': self.author,
            'rating': self.rating,
            'subject': self.subject,
            'body': self.body,
            'published_at': self.published_at.strftime('%Y-%m-%d') if self.published_at else None,
            'sentiment': self.sentiment,
            'received_at': est_time.strftime('%B %d, %Y %I %p EST')
        }
