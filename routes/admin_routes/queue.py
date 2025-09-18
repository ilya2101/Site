import os

from flask import Blueprint, abort, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename, send_from_directory
from datetime import datetime



from utils.allowed_file import allowed_file

from database.engine import db
from database.models.inService import InService
from database.models.queue import Queue
from flask import current_app
queue_bp = Blueprint("admin_queue", __name__, url_prefix="/admin")













@queue_bp.route('/admin/queue')
@login_required
def view_queue():
    if not current_user.is_admin:
        abort(403)

    # Получаем все записи из очереди
    queue_entries = Queue.query.order_by(Queue.moved_at.desc()).all()
    return render_template('admin_queue.html',
                           queue_entries=queue_entries,
                           user=current_user)

@queue_bp.route('/admin/queue/update/<int:queue_id>', methods=['POST'])
@login_required
def update_queue(queue_id):
    if not current_user.is_admin:
        abort(403)

    try:
        queue_entry = Queue.query.get_or_404(queue_id)

        # Обновляем данные
        queue_entry.name = request.form.get('name')
        queue_entry.phone = request.form.get('phone')
        queue_entry.car_brand = request.form.get('car_brand')
        queue_entry.car_model = request.form.get('car_model')
        queue_entry.desired_date = datetime.strptime(request.form.get('desired_date'), '%Y-%m-%d').date()
        queue_entry.desired_time = datetime.strptime(request.form.get('desired_time'), '%H:%M').time()
        queue_entry.comment = request.form.get('comment', '')

        db.session.commit()
        flash('Запись в очереди успешно обновлена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении записи: {str(e)}', 'danger')

    return redirect(url_for('view_queue'))

@queue_bp.route('/admin/queue/comment/<int:queue_id>', methods=['POST'])
@login_required
def add_queue_comment(queue_id):
    if not current_user.is_admin:
        abort(403)

    try:
        queue_entry = Queue.query.get_or_404(queue_id)
        comment = request.form.get('comment', '').strip()

        if comment:
            if queue_entry.comment:
                queue_entry.comment += f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M')}]: {comment}"
            else:
                queue_entry.comment = f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}]: {comment}"

            db.session.commit()
            flash('Комментарий добавлен!', 'success')
        else:
            flash('Комментарий не может быть пустым', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении комментария: {str(e)}', 'danger')

    return redirect(url_for('view_queue'))

@queue_bp.route('/admin/queue/to_service/<int:queue_id>', methods=['POST'])
@login_required
def move_to_service(queue_id):
    if not current_user.is_admin:
        abort(403)

    try:
        queue_entry = Queue.query.get_or_404(queue_id)

        # Обработка загрузки файла
        excel_filename = None
        if 'excel_file' in request.files:
            file = request.files['excel_file']
            if file and file.filename and allowed_file(file.filename):
                # Создаем безопасное имя файла
                filename = secure_filename(file.filename)
                # Добавляем timestamp для уникальности
                import time
                timestamp = str(int(time.time()))
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"

                # Сохраняем файл
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                excel_filename = filename


        # Создаем запись в ремонте
        service_entry = InService(
            queue_id=queue_entry.id,
            name=queue_entry.name,
            phone=queue_entry.phone,
            car_brand=queue_entry.car_brand,
            car_model=queue_entry.car_model,
            desired_date=queue_entry.desired_date,
            desired_time=queue_entry.desired_time,
            created_at=queue_entry.created_at,
            comment=queue_entry.comment,
            estimated_completion=datetime.strptime(request.form.get('estimated_completion'), '%Y-%m-%d').date() if request.form.get('estimated_completion') else None,
            estimated_cost=request.form.get('estimated_cost', ''),
            work_list=request.form.get('work_list', ''),
            excel_file=excel_filename
        )

        # Добавляем в ремонт и удаляем из очереди
        db.session.add(service_entry)
        db.session.delete(queue_entry)
        db.session.commit()

        flash('Автомобиль перемещен в ремонт!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при перемещении в ремонт: {str(e)}', 'danger')
        raise e

    return redirect(url_for('view_service'))

@queue_bp.route('/admin/queue/delete/<int:queue_id>')
@login_required
def delete_queue(queue_id):
    if not current_user.is_admin:
        abort(403)

    try:
        queue_entry = Queue.query.get_or_404(queue_id)
        db.session.delete(queue_entry)
        db.session.commit()
        flash('Запись из очереди удалена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении записи: {str(e)}', 'danger')

    return redirect(url_for('view_queue'))


@queue_bp.route('/view/excel/<filename>')
@login_required
def view_excel(filename):
    if not current_user.is_admin:
        abort(403)

    try:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=False
        )
    except:
        abort(404)