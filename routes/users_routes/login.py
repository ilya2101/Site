# routes/user.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, login_required, logout_user, current_user, current_user
from werkzeug.security import check_password_hash

from database.engine import db
from database.models.user import User
from utils.phone_utils import normalize_phone_number

user_bp = Blueprint('user', __name__)


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('Вы уже авторизованы!', 'info')
        return redirect(url_for('index.index'))

    if request.method == 'POST':
        phone_raw = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        if not phone_raw:
            flash('Введите номер телефона!', 'error')
            return render_template('login.html')

        if not password:
            flash('Введите пароль!', 'error')
            return render_template('login.html', phone=phone_raw)

        phone_normalized, error_msg = normalize_phone_number(phone_raw)
        if error_msg:
            flash(error_msg, 'error')
            return render_template('login.html', phone=phone_raw)

        user = User.query.filter_by(phone=phone_normalized).first()

        if not user or not check_password_hash(user.password, password):
            flash('Неверный номер телефона или пароль', 'error')
            return render_template('login.html', phone=phone_raw)

        login_user(user, remember=True)
        flash('Вы успешно вошли в систему!', 'success')

        return redirect(url_for('admin.admin_dashboard') if user.is_admin else url_for('index.index'))

    return render_template('login.html')


@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index.index'))