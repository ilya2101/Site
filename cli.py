"""
cli.py
Командная строка для управления задачами
"""

import click
from flask import current_app
from tasks.db_cleaner import run_all_cleanup_tasks
from tasks.scheduler import list_scheduled_jobs, start_scheduler, stop_scheduler

@click.group()
def cli():
    """Команды для управления задачами"""
    pass

@cli.command()
def cleanup():
    """Запустить очистку базы данных вручную"""
    click.echo("🧹 Запуск очистки БД...")
    results = run_all_cleanup_tasks()
    click.echo(f"✅ Результаты: {results}")

@cli.command()
def scheduler_start():
    """Запустить планировщик задач"""
    if start_scheduler():
        click.echo("✅ Планировщик запущен")
    else:
        click.echo("⚠️ Планировщик уже запущен")

@cli.command()
def scheduler_stop():
    """Остановить планировщик задач"""
    if stop_scheduler():
        click.echo("✅ Планировщик остановлен")
    else:
        click.echo("⚠️ Планировщик уже остановлен")

@cli.command()
def scheduler_list():
    """Показать список запланированных задач"""
    jobs = list_scheduled_jobs()
    if jobs:
        click.echo("📅 Запланированные задачи:")
        for job in jobs:
            click.echo(f"  • {job['name']}")
            click.echo(f"    ID: {job['id']}")
            click.echo(f"    Следующий запуск: {job['next_run']}")
            click.echo(f"    Расписание: {job['trigger']}")
            click.echo()
    else:
        click.echo("📭 Нет запланированных задач")

if __name__ == '__main__':
    cli()