from datetime import datetime
from database.engine import db


class Queue(db.Model):
    __tablename__ = 'queue'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    car_brand = db.Column(db.String(50), nullable=False)
    car_model = db.Column(db.String(50), nullable=False)
    desired_date = db.Column(db.Date, nullable=False)
    desired_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='in_queue')
    comment = db.Column(db.Text, default='')
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с оригинальной заявкой
    application = db.relationship('Application', backref='queue_entries')