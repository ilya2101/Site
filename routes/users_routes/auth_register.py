# routes/auth_register.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from database.engine import db
from database.models.user import User
from utils.phone_utils import normalize_phone_number

# Создаём блюпринт
# Имя 'register' — более логичное и короткое, чем 'auth_register'
register_bp = Blueprint('register', __name__)


@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Вы уже авторизованы!', 'info')
        return redirect(url_for('index.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone_raw = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Базовая валидация
        errors = []

        if not first_name or len(first_name) < 2:
            errors.append('Имя должно быть не менее 2 символов')

        if not last_name or len(last_name) < 2:
            errors.append('Фамилия должна быть не менее 2 символов')

        if not phone_raw:
            errors.append('Введите номер телефона')

        if not password:
            errors.append('Введите пароль')
        elif len(password) < 6:
            errors.append('Пароль должен быть не менее 6 символов')
        elif password != confirm_password:
            errors.append('Пароли не совпадают')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html',
                                   first_name=first_name,
                                   last_name=last_name,
                                   phone=phone_raw)

        # Нормализация телефона
        phone_normalized, error_msg = normalize_phone_number(phone_raw)
        if error_msg:
            flash(error_msg, 'error')
            return render_template('register.html',
                                   first_name=first_name,
                                   last_name=last_name,
                                   phone=phone_raw)

        # Проверка на дубликат
        if User.query.filter_by(phone=phone_normalized).first():
            flash('Этот номер телефона уже зарегистрирован', 'error')
            return render_template('register.html',
                                   first_name=first_name,
                                   last_name=last_name,
                                   phone=phone_raw)

        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            new_user = User(
                first_name=first_name,
                last_name=last_name,
                phone=phone_normalized,
                password=hashed_password,
                is_admin=False  # явно указываем, если нужно
            )

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=True)
            flash('Регистрация успешна! Добро пожаловать!', 'success')
            return redirect(url_for('index.index'))

        except IntegrityError:
            db.session.rollback()
            flash('Ошибка при регистрации. Возможно, номер уже используется.', 'error')
            current_app.logger.warning(f"IntegrityError при регистрации телефона: {phone_normalized}")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Неожиданная ошибка при регистрации: {e}")
            flash('Произошла неожиданная ошибка при регистрации.', 'error')

        # Если что-то пошло не так — возвращаем форму
        return render_template('register.html',
                               first_name=first_name,
                               last_name=last_name,
                               phone=phone_raw)

    # GET-запрос
    return render_template('register.html')