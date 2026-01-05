from datetime import datetime

from database.engine import db



class EmailAttempt(db.Model):
    __tablename__ = 'email_attempts'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, index=True)  # индекс для быстрого поиска
    ip_address = db.Column(db.String(45), nullable=False)  # IPv4 (15) или IPv6 (45)
    user_agent = db.Column(db.Text)  # браузер/устройство пользователя
    confirmation_code = db.Column(db.String(20))  # для логов
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Опционально: связь с пользователем (если уже зарегистрирован)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f'<EmailAttempt {self.email} at {self.sent_at}>'