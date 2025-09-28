import os
from datetime import datetime

from flask import Blueprint, abort, render_template, request
from flask import current_app
from flask import send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename, redirect

from database.engine import db
from utils.allowed_file import allowed_file

service_bp = Blueprint('admin_service', __name__, url_prefix='/admin/service')








@service_bp.route('/admin/service')
@login_required
def view_service():
    if not current_user.is_admin:
        abort(403)

    # Получаем все записи в ремонте
    service_entries = InService.query.order_by(InService.moved_at.desc()).all()
    return render_template('admin_service.html',
                           service_entries=service_entries,
                           user=current_user)

@service_bp.route('/admin/service/update/<int:service_id>', methods=['POST'])
@login_required
def update_service(service_id, conf=None):
    if not current_user.is_admin:
        abort(403)

    try:
        service_entry = InService.query.get_or_404(service_id)

        # Обработка загрузки нового файла
        if 'excel_file' in request.files:
            file = request.files['excel_file']
            if file and file.filename and allowed_file(file.filename):
                # Удаляем старый файл, если он есть
                if service_entry.excel_file:
                    try:
                        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], service_entry.excel_file))
                    except:
                        pass

                # Создаем безопасное имя файла

                # Создаем безопасное имя файла
                filename = secure_filename(file.filename)
                import time
                timestamp = str(int(time.time()))
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"

                # Сохраняем новый файл
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                service_entry.excel_file = filename


# Обновляем данные
        service_entry.name = request.form.get('name')
        service_entry.phone = request.form.get('phone')
        service_entry.car_brand = request.form.get('car_brand')
        service_entry.car_model = request.form.get('car_model')
        service_entry.estimated_completion = datetime.strptime(request.form.get('estimated_completion'), '%Y-%m-%d').date() if request.form.get('estimated_completion') else None
        service_entry.estimated_cost = request.form.get('estimated_cost', '')
        service_entry.comment = request.form.get('comment', '')
        service_entry.work_list = request.form.get('work_list', '')

        db.session.commit()
        flash('Запись в ремонте успешно обновлена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении записи: {str(e)}', 'danger')

    return redirect(url_for('admin_service.view_service'))






@service_bp.route('/admin/service/delete/<int:service_id>')
@login_required
def delete_service(service_id):
    if not current_user.is_admin:
        abort(403)

    try:
        service_entry = InService.query.get_or_404(service_id)

        # Удаляем файл, если он есть
        if service_entry.excel_file:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], service_entry.excel_file))
            except:
                pass

        db.session.delete(service_entry)
        db.session.commit()
        flash('Запись из ремонта удалена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении записи: {str(e)}', 'danger')

    return redirect(url_for('admin_service.view_service'))


from database.models.inService import InService
from database.models.completed_service import CompletedService
from flask import redirect, url_for, flash

@service_bp.route('/complete/<int:id>', methods=['POST'])
@login_required
def complete_service(id):
    service = InService.query.get_or_404(id)

    # Приведение стоимости к числу
    estimated_cost = service.estimated_cost
    if estimated_cost == '' or estimated_cost is None:
        estimated_cost = None
    else:
        estimated_cost = float(estimated_cost)

    # Создаём копию в CompletedService
    completed = CompletedService(
        queue_id=service.queue_id,
        name=service.name,
        phone=service.phone,
        car_brand=service.car_brand,
        car_model=service.car_model,
        desired_date=service.desired_date,
        desired_time=service.desired_time,
        created_at=service.created_at,
        estimated_completion=service.estimated_completion,
        estimated_cost=estimated_cost,
        comment=service.comment,
        work_list=service.work_list,
        excel_file=service.excel_file,
        moved_at=datetime.utcnow()
    )

    db.session.add(completed)
    db.session.delete(service)
    db.session.commit()

    flash('Услуга успешно завершена и перенесена в архив', 'success')

    return redirect(url_for('admin_service.view_service'))










@service_bp.route('/admin/view/excel/<path:filename>')
@login_required
def view_excel(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

