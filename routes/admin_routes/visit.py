from flask import Blueprint, request, render_template
from flask_login import current_user, login_required
from datetime import datetime, date
from database.models.visit import Visit
from database.engine import db

visit_bp = Blueprint("visit", __name__, url_prefix="/admin/visit")

@visit_bp.before_app_request
def log_visit():
    today = datetime.utcnow().date()

    if current_user.is_authenticated:
        # Проверяем по user_id
        existing_visit = Visit.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        if not existing_visit:
            new_visit = Visit(
                user_id=current_user.id,
                ip=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
                date=today
            )
            db.session.add(new_visit)
            db.session.commit()
    else:
        # Проверяем по ip + user_agent
        existing_visit = Visit.query.filter_by(
            ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            date=today
        ).first()
        if not existing_visit:
            new_visit = Visit(
                user_id=None,
                ip=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
                date=today
            )
            db.session.add(new_visit)
            db.session.commit()


@visit_bp.route("/", endpoint="stats")
@login_required
def stats():
    if not current_user.is_admin:
        return "Доступ запрещён", 403

    today = date.today()
    now = datetime.now()

    # Счётчики
    count_day = Visit.query.filter_by(date=today).count()

    first_of_month = date(now.year, now.month, 1)
    count_month = Visit.query.filter(
        Visit.date >= first_of_month, Visit.date <= today
    ).count()

    first_of_year = date(now.year, 1, 1)
    count_year = Visit.query.filter(
        Visit.date >= first_of_year, Visit.date <= today
    ).count()

    count_day_guests = Visit.query.filter_by(date=today, user_id=None).count()
    count_day_users = Visit.query.filter(
        Visit.date == today, Visit.user_id != None
    ).count()

    visits = Visit.query.order_by(Visit.date.desc()).limit(50).all()

    return render_template(
        "visit_stats.html",
        count_day=count_day,
        count_month=count_month,
        count_year=count_year,
        count_day_guests=count_day_guests,
        count_day_users=count_day_users,
        visits=visits
    )
