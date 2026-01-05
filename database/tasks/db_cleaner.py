"""
tasks/db_cleaner.py
Модуль для очистки базы данных от устаревших данных
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import text

from database.engine import db
from database.models.EmailAttempt import EmailAttempt

logger = logging.getLogger(__name__)

def cleanup_email_attempts(days_to_keep=30):
    """
    Удаляет старые записи о попытках отправки email

    Args:
        days_to_keep (int): Сколько дней хранить записи (по умолчанию 30)

    Returns:
        int: Количество удаленных записей
    """
    try:
        # Рассчитываем дату "старее которой удаляем"
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        logger.info(f"🧹 Начинаем очистку EmailAttempt старше {cutoff_date}")

        # Удаляем записи старее cutoff_date
        deleted_count = EmailAttempt.query.filter(
            EmailAttempt.created_at < cutoff_date
        ).delete(synchronize_session=False)

        db.session.commit()

        logger.info(f"✅ Удалено {deleted_count} старых записей EmailAttempt")
        return deleted_count

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Ошибка при очистке EmailAttempt: {e}")
        return 0


def cleanup_expired_sessions():
    """
    Очищает Flask сессии с истекшими данными регистрации
    Этот метод зависит от того, как хранятся сессии (БД, Redis, файлы)
    """
    try:
        # Если сессии хранятся в БД (Flask-Session)
        # Пример для Flask-Session с SQLAlchemy:
        # from flask_session.sessions import Session
        # Session.query.filter(Session.expiry < datetime.utcnow()).delete()

        logger.info("ℹ️ Очистка сессий требует настройки Flask-Session")
        return 0

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке сессий: {e}")
        return 0


def cleanup_unconfirmed_users(days_to_keep=7):
    """
    Удаляет пользователей, которые не подтвердили email за N дней

    Args:
        days_to_keep (int): Сколько дней хранить неподтвержденных пользователей

    Returns:
        int: Количество удаленных пользователей
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        logger.info(f"🧹 Очистка неподтвержденных пользователей старше {cutoff_date}")

        # Ищем пользователей, которые:
        # 1. Не подтвердили email (email_confirmed = False)
        # 2. Были созданы более days_to_keep дней назад
        # 3. Нет связанных заказов или другой важной информации
        from database.models.user import User

        deleted_count = User.query.filter(
            User.email_confirmed == False,
            User.created_at < cutoff_date,
            # Добавьте дополнительные условия, если нужно
            # Например, проверить что нет заказов
        ).delete(synchronize_session=False)

        db.session.commit()

        logger.info(f"✅ Удалено {deleted_count} неподтвержденных пользователей")
        return deleted_count

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Ошибка при очистке неподтвержденных пользователей: {e}")
        return 0


def run_all_cleanup_tasks():
    """
    Запускает все задачи очистки
    """
    logger.info("🚀 Запуск всех задач очистки БД")

    results = {
        'email_attempts': cleanup_email_attempts(days_to_keep=30),
        'expired_sessions': cleanup_expired_sessions(),
        'unconfirmed_users': cleanup_unconfirmed_users(days_to_keep=7),
    }

    logger.info(f"📊 Результаты очистки: {results}")
    return results


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Запуск очистки при прямом вызове скрипта
    print("🔄 Запуск очистки базы данных...")
    results = run_all_cleanup_tasks()
    print(f"✅ Очистка завершена. Результаты: {results}")