import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from database.engine import db
from database.models.EmailAttempt import EmailAttempt
from app import app

with app.app_context():
    print("📝 Добавляем тестовые данные...")
    
    # Текущее время
    now = datetime.utcnow()
    
    # 1. Очень старая запись (35 дней назад) - должна быть удалена
    very_old = EmailAttempt(
        email="very_old@test.com",
        ip_address="192.168.1.100",
        user_agent="Test Browser",
        confirmation_code="OLD001",
        sent_at=now - timedelta(days=35),
        created_at=now - timedelta(days=35)
    )
    
    # 2. Старая запись (32 дня назад) - должна быть удалена
    old = EmailAttempt(
        email="old@test.com",
        ip_address="192.168.1.101",
        user_agent="Test Browser",
        confirmation_code="OLD002",
        sent_at=now - timedelta(days=32),
        created_at=now - timedelta(days=32)
    )
    
    # 3. Немного старая запись (25 дней назад) - НЕ должна быть удалена
    recent = EmailAttempt(
        email="recent@test.com",
        ip_address="192.168.1.102",
        user_agent="Test Browser",
        confirmation_code="RECENT1",
        sent_at=now - timedelta(days=25),
        created_at=now - timedelta(days=25)
    )
    
    # 4. Совсем новая запись (5 дней назад) - НЕ должна быть удалена
    new = EmailAttempt(
        email="new@test.com",
        ip_address="192.168.1.103",
        user_agent="Test Browser",
        confirmation_code="NEW001",
        sent_at=now - timedelta(days=5),
        created_at=now - timedelta(days=5)
    )
    
    # 5. Очень новая запись (сегодня) - НЕ должна быть удалена
    very_new = EmailAttempt(
        email="very_new@test.com",
        ip_address="192.168.1.104",
        user_agent="Test Browser",
        confirmation_code="NEW002",
        sent_at=now,
        created_at=now
    )
    
    # Добавляем все записи
    db.session.add_all([very_old, old, recent, new, very_new])
    db.session.commit()
    
    # Проверяем
    total = EmailAttempt.query.count()
    print(f"✅ Добавлено {total} тестовых записей")
    
    # Покажем все записи
    print("\n📋 Все записи в таблице:")
    attempts = EmailAttempt.query.order_by(EmailAttempt.created_at).all()
    for attempt in attempts:
        days_ago = (now - attempt.created_at).days
        print(f"  • {attempt.email} - {days_ago} дней назад - код: {attempt.confirmation_code}")
