from flask import Blueprint, abort, render_template
from flask_login import login_required, current_user
from datetime import datetime


from database.models.application import Application
from database.models.queue import Queue

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")




@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)

    # Получаем статистику
    new_requests_count = Application.query.filter_by(status='new').count()
    queue_count = Queue.query.count()
    total_requests = Application.query.count()

    # Получаем последние 5 заявок
    recent_requests = Application.query.order_by(Application.created_at.desc()).limit(5).all()

    return render_template('admin_dashboard.html',
                           user=current_user,
                           now=datetime.now(),
                           new_requests_count=new_requests_count,
                           queue_count=queue_count,
                           total_requests=total_requests,
                           recent_requests=recent_requests)