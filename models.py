from datetime import datetime
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

    def to_dict(self):
        return {
            'author': self.author,
            'rating': self.rating,
            'subject': self.subject,
            'body': self.body,
            'published_at': self.published_at.strftime('%Y-%m-%d') if self.published_at else None,
            'sentiment': self.sentiment,
            'received_at': self.received_at.strftime('%Y-%m-%d %H:%M:%S')
        }
