# check_db_users.py
from app import app, db
from database.models.user import User

print("🔍 Проверяем пользователей в базе...")

with app.app_context():
    users = User.query.all()

    if not users:
        print("✅ База пустая - нет пользователей")
    else:
        print(f"📊 Найдено пользователей: {len(users)}")
        print("=" * 60)

        for user in users:
            print(f"ID: {user.id}")
            print(f"  Имя: {user.first_name} {user.last_name}")
            print(f"  Телефон: '{user.phone}'")
            print(f"  Email: {user.email}")
            print(f"  Email подтвержден: {user.email_confirmed}")
            print("-" * 40)