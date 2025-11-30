from datetime import datetime
from database.engine import db

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)  # Изменил на Text для PostgreSQL
    date = db.Column(db.Date, default=datetime.utcnow)  # Убрал .date