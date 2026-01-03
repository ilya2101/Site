# clear_users.py
from database.engine import db
from database.models.user import User
from app import app  # Импортируй свое приложение Flask

def clear_users():
    with app.app_context():  # <-- Добавь контекст приложения
        try:
            # Подсчитать перед удалением
            count = User.query.count()
            print(f"Найдено пользователей: {count}")

            if count > 0:
                # Удалить всех
                User.query.delete()
                db.session.commit()
                print(f"✅ Удалено {count} пользователей")
            else:
                print("✅ Пользователей нет в базе")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    clear_users()