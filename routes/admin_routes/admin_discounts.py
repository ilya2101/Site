import os
from datetime import date, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Blueprint, flash, redirect, url_for, request, render_template, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from sqlalchemy.sql.functions import current_date
from werkzeug.utils import secure_filename
from wtforms import StringField, TextAreaField, BooleanField, DateField
from wtforms.validators import DataRequired

from database.engine import db
from database.models.discount import Discount
from forms import DiscountForm

admin_discounts_bp = Blueprint("admin_discounts", __name__, url_prefix="/admin/discounts")



now = datetime.now()
current_date = date.today().isoformat()  # 'YYYY-MM-DD'






@admin_discounts_bp.route('/admin/discounts', methods=['GET', 'POST'])
@login_required
def admin_discounts():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index.index'))

    form = DiscountForm()
    discounts = Discount.query.order_by(Discount.created_at.desc()).all()


    now = datetime.now()


    if request.method == 'POST':
        if form.validate_on_submit():
            discount = Discount(
                title=form.title.data,
                description=form.description.data,
                is_active=form.is_active.data,
                expires_at=form.expires_at.data
            )

            # Обработка загрузки изображения
            if form.image.data:
                try:
                    # Создаем папку если ее нет
                    upload_folder = 'static/uploads/discounts'
                    os.makedirs(upload_folder, exist_ok=True)

                    filename = secure_filename(form.image.data.filename)
                    unique_filename = f"{datetime.now().timestamp()}_{filename}"
                    filepath = os.path.join(upload_folder, unique_filename)

                    # Сохраняем файл
                    form.image.data.save(filepath)
                    discount.image = f"uploads/discounts/{unique_filename}"

                except Exception as e:
                    flash(f'Ошибка при загрузке изображения: {str(e)}', 'error')
                    return redirect(url_for('admin_discounts.admin_discounts'))

            try:
                db.session.add(discount)
                db.session.commit()
                flash('Скидка успешно добавлена!', 'success')
                return redirect(url_for('admin_discounts.admin_discounts'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при сохранении: {str(e)}', 'error')
                return redirect(url_for('admin_discounts.admin_discounts'))

    return render_template('admin_discounts.html',
                           form=form,
                           discounts=discounts,
                           user=current_user,
                           now=now,
                           current_date=current_date)




@admin_discounts_bp.route('/admin/discount/delete/<int:id>', methods=['POST'])
@login_required
def delete_discount(id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index.index'))

    discount = Discount.query.get_or_404(id)

    try:
        # Удаляем изображение если есть
        if discount.image:
            try:
                image_path = os.path.join('static', discount.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                flash(f'Ошибка при удалении изображения: {str(e)}', 'warning')

        # Удаляем из базы
        db.session.delete(discount)
        db.session.commit()
        flash('Скидка успешно удалена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')

    return redirect(url_for('admin_discounts.admin_discounts'))



@admin_discounts_bp.route('/admin/cleanup_expired', methods=['POST'])
@login_required
def admin_cleanup_expired():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Доступ запрещен'})

    try:
        deleted_count = cleanup_expired_discounts()
        return jsonify({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



@admin_discounts_bp.route('/edit/<int:id>')
@login_required
def edit_discount_form(id):
    if not current_user.is_admin:
        return "Доступ запрещен", 403

    discount = Discount.query.get_or_404(id)

    # Создаем форму с данными скидки
    class EditDiscountForm(FlaskForm):
        title = StringField('Название', validators=[DataRequired()], default=discount.title)
        description = TextAreaField('Описание', validators=[DataRequired()], default=discount.description)
        is_active = BooleanField('Активна', default=discount.is_active)
        expires_at = DateField('Действует до', format='%Y-%m-%d', default=discount.expires_at)

    form = EditDiscountForm()

    from datetime import date
    current_date = date.today().isoformat()  # Для min в input type="date"

    # Возвращаем только partial-шаблон с формой для модального окна
    return render_template('partials/edit_discount_form.html',
                           form=form,
                           discount=discount,
                           current_date=current_date)




@admin_discounts_bp.route('/update/<int:id>', methods=['POST'])
@login_required
def update_discount(id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('admin_discounts.admin_discounts'))

    discount = Discount.query.get_or_404(id)

    try:
        discount.title = request.form.get('title')
        discount.description = request.form.get('description')
        discount.is_active = 'is_active' in request.form
        expires_at = request.form.get('expires_at')
        discount.expires_at = datetime.strptime(expires_at, '%Y-%m-%d') if expires_at else None

        db.session.commit()
        flash('Скидка успешно обновлена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении: {str(e)}', 'error')

    return redirect(url_for('admin_discounts.admin_discounts'))


def cleanup_expired_discounts():
    """Удаляет просроченные скидки"""
    try:
        expired_count = Discount.query.filter(
            Discount.expires_at.isnot(None),
            Discount.expires_at < datetime.now()
        ).delete(synchronize_session=False)

        db.session.commit()
        print(f"Удалено {expired_count} просроченных скидок")
        return expired_count
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении просроченных скидок: {e}")
        return 0


scheduler = BackgroundScheduler()
scheduler.add_job(
    func=cleanup_expired_discounts,
    trigger=IntervalTrigger(hours=1),
    id='cleanup_discounts',
    name='Cleanup expired discounts',
    replace_existing=True
)
scheduler.start()