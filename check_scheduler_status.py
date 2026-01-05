import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

with app.app_context():
    print("🔍 Проверка состояния планировщика...")
    
    # Проверяем работает ли планировщик
    try:
        from database.tasks.scheduler import scheduler
        
        if scheduler.running:
            print("✅ Планировщик работает")
            jobs = scheduler.get_jobs()
            print(f"📅 Количество запланированных задач: {len(jobs)}")
            
            for job in jobs:
                print(f"\n  Задача: {job.name}")
                print(f"    ID: {job.id}")
                print(f"    Следующий запуск: {job.next_run_time}")
                print(f"    Триггер: {job.trigger}")
        else:
            print("⚠️ Планировщик не запущен")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке планировщика: {e}")
        import traceback
        traceback.print_exc()
