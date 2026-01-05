"""
tasks/scheduler.py
Планировщик для периодического запуска задач
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

logger = logging.getLogger(__name__)

# Создаем планировщик
scheduler = BackgroundScheduler()

def setup_scheduled_tasks():
    """
    Настраивает расписание для всех автоматических задач
    """
    try:
        # Импортируем задачи очистки
        from .db_cleaner import run_all_cleanup_tasks

        # 1. Очистка старых записей EmailAttempt - 1 числа каждого месяца в 3:00
        scheduler.add_job(
            run_all_cleanup_tasks,
            trigger=CronTrigger(day=1, hour=3, minute=0),  # 1 число, 3:00 утра
            id='monthly_db_cleanup',
            name='Ежемесячная очистка БД',
            replace_existing=True
        )

        logger.info("✅ Планировщик задач настроен")

        # Можно добавить больше задач:
        # - Ежедневная проверка чего-то
        # - Еженедельная отправка отчетов
        # - и т.д.

    except Exception as e:
        logger.error(f"❌ Ошибка настройки планировщика: {e}")
        raise


def start_scheduler():
    """
    Запускает планировщик
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("🚀 Планировщик задач запущен")
        return True
    return False


def stop_scheduler():
    """
    Останавливает планировщик
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Планировщик задач остановлен")
        return True
    return False


def list_scheduled_jobs():
    """
    Возвращает список запланированных задач
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    return jobs


if __name__ == "__main__":
    # Настройка логирования для теста
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🔧 Тестирование планировщика...")

    # Настраиваем задачи
    setup_scheduled_tasks()

    # Запускаем планировщик
    start_scheduler()

    # Показываем запланированные задачи
    print("\n📅 Запланированные задачи:")
    for job in list_scheduled_jobs():
        print(f"  - {job['name']}: {job['trigger']}")

    print("\n✅ Планировщик запущен. Нажмите Ctrl+C для остановки.")

    try:
        # Бесконечный цикл для тестирования
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()
        print("\n🛑 Планировщик остановлен")