from datetime import datetime

from flask import Blueprint, abort, render_template, request, flash, redirect, url_for, Request
from flask_login import login_required, current_user

from database.engine import db
from database.models.application import Application
from database.models.queue import Queue


admin_required_bp = Blueprint("admin_required", __name__, url_prefix="/admin")








def requests():
    sort_by = request.args.get('sort_by', 'id')  # По умолчанию сортировка по ID
    order = request.args.get('order', 'asc')     # По умолчанию по возрастанию

    # Получаем список заявок
    requests_list = Request.query  # если используешь SQLAlchemy

    # Применяем сортировку
    if order == 'asc':
        requests_list = requests_list.order_by(getattr(Request, sort_by).asc())
    else:
        requests_list = requests_list.order_by(getattr(Request, sort_by).desc())

    requests_list = requests_list.all()

    # Функция для шаблона — определяет следующий порядок
    def next_order(column):
        if column == sort_by and order == 'asc':
            return 'desc'
        return 'asc'

    return render_template('admin_requests.html', requests=requests_list, next_order=next_order)


@admin_required_bp.route('/admin/requests')
@login_required
def view_requests():
    order = request.args.get('order', 'asc')

    # Сортировка по дате и времени записи
    requests_list = Application.query

    if order == 'asc':
        requests_list = requests_list.order_by(Application.desired_date.asc(), Application.desired_time.asc())
    else:
        requests_list = requests_list.order_by(Application.desired_date.desc(), Application.desired_time.desc())

    requests_list = requests_list.all()

    # Функция для шаблона — определяет следующий порядок
    def next_order():
        return 'desc' if order == 'asc' else 'asc'

    return render_template('admin_requests.html', requests=requests_list, next_order=next_order, current_order=order)

@admin_required_bp.route('/admin/request/update/<int:request_id>', methods=['POST'])
@login_required
def update_request(request_id):
    if not current_user.is_admin:
        abort(403)

    try:
        application = Application.query.get_or_404(request_id)

        # Обновляем данные
        application.name = request.form.get('name')
        application.phone = request.form.get('phone')
        application.car_brand = request.form.get('car_brand')
        application.car_model = request.form.get('car_model')
        application.desired_date = datetime.strptime(request.form.get('desired_date'), '%Y-%m-%d').date()
        application.desired_time = datetime.strptime(request.form.get('desired_time'), '%H:%M').time()
        application.comment = request.form.get('comment', '')

        db.session.commit()
        flash('Заявка успешно обновлена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении заявки: {str(e)}', 'danger')

    return redirect(url_for('admin_required.view_requests'))




@admin_required_bp.route('/admin/request/comment/<int:request_id>', methods=['POST'])
@login_required
def add_comment(request_id):
    if not current_user.is_admin:
        abort(403)

    try:
        application = Application.query.get_or_404(request_id)
        comment = request.form.get('comment', '').strip()

        if comment:
            if application.comment:
                application.comment += f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M')}]: {comment}"
            else:
                application.comment = f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}]: {comment}"

            db.session.commit()
            flash('Комментарий добавлен!', 'success')
        else:
            flash('Комментарий не может быть пустым', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении комментария: {str(e)}', 'danger')

    return redirect(url_for('admin_required.view_requests'))

@admin_required_bp.route('/admin/request/confirm/<int:request_id>')
@login_required
def confirm_request(request_id):
    if not current_user.is_admin:
        abort(403)

    try:
        application = Application.query.get_or_404(request_id)
        application.status = "Обработана"

        # Создаем запись в очереди
        queue_entry = Queue(
            application_id=application.id,
            name=application.name,
            phone=application.phone,
            car_brand=application.car_brand,
            car_model=application.car_model,
            desired_date=application.desired_date,
            desired_time=application.desired_time,
            created_at=application.created_at,
            comment=application.comment,
            status='in_queue'
        )

        # Добавляем в очередь и удаляем из заявок
        db.session.add(queue_entry)
        db.session.commit()

        flash('Заявка перемещена в очередь!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при перемещении заявки: {str(e)}', 'danger')

    return redirect(url_for('admin_required.view_requests'))

@admin_required_bp.route('/admin/request/delete/<int:request_id>')
@login_required
def delete_request(request_id):
    if not current_user.is_admin:
        abort(403)

    try:
        application = Application.query.get_or_404(request_id)
        db.session.delete(application)
        db.session.commit()
        flash('Заявка удалена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении заявки: {str(e)}', 'danger')

    return redirect(url_for('admin_required.view_requests'))