from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    symbol = db.Column(db.String(20))
    direction = db.Column(db.String(4))
    entry_price = db.Column(db.Float)
    exit_price = db.Column(db.Float, nullable=True)
    result = db.Column(db.Integer, nullable=True)   # 1=win, 0=loss
    features_json = db.Column(db.Text, nullable=True)
