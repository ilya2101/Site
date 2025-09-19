from datetime import datetime

from sqlalchemy import Float

from database.engine import db


class InService(db.Model):
    __bind_key__ = 'applications'
    __tablename__ = 'in_service'

    id = db.Column(db.Integer, primary_key=True)
    queue_id = db.Column(db.Integer, db.ForeignKey('queue.id'))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    car_brand = db.Column(db.String(50), nullable=False)
    car_model = db.Column(db.String(50), nullable=False)
    desired_date = db.Column(db.Date, nullable=False)
    desired_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_completion = db.Column(db.Date, nullable=True)
    estimated_cost = db.Column(Float, nullable=True)
    comment = db.Column(db.Text, default='')
    work_list = db.Column(db.Text, default='')
    excel_file = db.Column(db.String(255), nullable=True)  # Путь к Excel файлу
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)



    queue_entry = db.relationship('Queue', backref='service_entries')