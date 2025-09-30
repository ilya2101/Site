from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import date, datetime
from database.models.visit import Visit
from database.engine import db

visit_bp = Blueprint('visit', __name__, url_prefix='/admin/visit')

@visit_bp.route('/')
@login_required
def stats():
    if not current_user.is_admin:
        return "Доступ запрещен", 403

    today = date.today()
    now = datetime.now()

    count_day = Visit.query.filter_by(date=today).count()

    first_of_month = date(now.year, now.month, 1)
    count_month = Visit.query.filter(Visit.date >= first_of_month, Visit.date <= today).count()

    first_of_year = date(now.year, 1, 1)
    count_year = Visit.query.filter(Visit.date >= first_of_year, Visit.date <= today).count()

    count_day_guests = Visit.query.filter_by(date=today, user_id=None).count()
    count_day_users = Visit.query.filter(Visit.date == today, Visit.user_id != None).count()

    return render_template("visit_stats.html",
                           count_day=count_day,
                           count_month=count_month,
                           count_year=count_year,
                           count_day_guests=count_day_guests,
                           count_day_users=count_day_users)
