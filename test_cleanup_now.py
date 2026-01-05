import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from database.engine import db
from database.models.EmailAttempt import EmailAttempt
from app import app

with app.app_context():
    print("🧹 Тестирование очистки БД...")
    
    # Проверяем до очистки
    before_count = EmailAttempt.query.count()
    print(f"📊 Записей ДО очистки: {before_count}")
    
    # Запускаем очистку (удаляем старше 30 дней)
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    deleted = EmailAttempt.query.filter(
        EmailAttempt.created_at < cutoff_date
    ).delete(synchronize_session=False)
    
    db.session.commit()
    
    print(f"🗑️ Удалено записей: {deleted}")
    
    # Проверяем после очистки
    after_count = EmailAttempt.query.count()
    print(f"📊 Записей ПОСЛЕ очистки: {after_count}")
    
    # Покажем оставшиеся записи
    print("\n📋 Оставшиеся записи:")
    remaining = EmailAttempt.query.order_by(EmailAttempt.created_at).all()
    now = datetime.utcnow()
    
    if remaining:
        for attempt in remaining:
            days_ago = (now - attempt.created_at).days
            print(f"  • {attempt.email} - {days_ago} дней назад - код: {attempt.confirmation_code}")
    else:
        print("  (нет записей)")
    
    print(f"\n✅ Ожидаемый результат: удалено 2 записи (старше 30 дней), осталось 3 записи")
