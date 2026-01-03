from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from database.engine import db
from database.models.user import User

# Создаем один Blueprint для пользователей (УБЕРИТЕ ПОВТОРНОЕ СОЗДАНИЕ)
user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        user = User.query.filter_by(phone=phone).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.is_admin:
                flash('Вы успешно вошли как администратор!', 'success')
                return redirect(url_for('admin.admin_dashboard'))
            else:
                flash('Вы успешно вошли!', 'success')
                return redirect(url_for('index.index'))
        else:
            flash('Неверный номер или пароль!', 'danger')

    return render_template('login.html')


@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли!', 'success')
    return redirect(url_for('index.index'))




@user_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        try:
            user = current_user
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            user.phone = request.form['phone']

            db.session.commit()
            flash('Профиль успешно обновлен!', 'success')

        except Exception:
            db.session.rollback()
            flash('Ошибка при обновлении профиля', 'error')

    return redirect(url_for('account'))