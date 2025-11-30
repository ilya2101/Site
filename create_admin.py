import os
import sys
sys.path.append(os.path.dirname(__file__))

from app import app
from database.engine import db
from database.models.user import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Создаем первого админа
    admin1 = User.query.filter_by(phone="+71234567890").first()
    if not admin1:
        admin1 = User(
            first_name="Admin",
            last_name="Main",
            phone="+71234567890",
            password=generate_password_hash("secret123"),
            is_admin=True
        )
        db.session.add(admin1)
        print("Первый админ создан")

    # Создаем второго админа
    admin2 = User.query.filter_by(phone="+79876543210").first()
    if not admin2:
        admin2 = User(
            first_name="Manager",
            last_name="Second",
            phone="+79876543210",
            password=generate_password_hash("password123"),
            is_admin=True
        )
        db.session.add(admin2)
        print("Второй админ создан")

    db.session.commit()
    print("Все админы созданы!")