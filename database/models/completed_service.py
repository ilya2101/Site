
from database.engine import db
from datetime import datetime

class CompletedService(db.Model):
    __tablename__ = 'completed_service'

    id = db.Column(db.Integer, primary_key=True)
    queue_id = db.Column(db.Integer, db.ForeignKey('queue.id'))  # Добавить ForeignKey
    name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    car_brand = db.Column(db.String(50))
    car_model = db.Column(db.String(50))
    desired_date = db.Column(db.Date)
    desired_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Исправить на utcnow
    estimated_completion = db.Column(db.DateTime)
    estimated_cost = db.Column(db.Numeric(10, 2))  # Исправить на Numeric
    comment = db.Column(db.Text)
    work_list = db.Column(db.Text)
    excel_file = db.Column(db.String(200))
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)  # Исправить на utcnow