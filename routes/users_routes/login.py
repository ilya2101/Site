import phonenumbers
from phonenumbers import NumberParseException
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError

from database.engine import db
from database.models.user import User

user_bp = Blueprint('user', __name__)


def normalize_phone_number(phone_raw):
    """Нормализует номер телефона"""
    if not phone_raw or not phone_raw.strip():
        return None, 'Введите номер телефона!'

    try:
        # Убираем все нецифровые символы кроме плюса
        cleaned = ''.join(c for c in phone_raw if c.isdigit() or c == '+')

        # Если номер начинается с 8, меняем на +7
        if cleaned.startswith('8'):
            cleaned = '+7' + cleaned[1:]
        # Если номер начинается с 7 без плюса, добавляем плюс
        elif cleaned.startswith('7') and not cleaned.startswith('+7'):
            cleaned = '+' + cleaned

        # Парсим номер
        parsed = phonenumbers.parse(cleaned, "RU")

        if not phonenumbers.is_valid_number(parsed):
            return None, 'Неверный формат номера! Используйте: +79991234567'

        normalized = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return normalized, None

    except NumberParseException:
        return None, 'Неверный формат номера! Используйте: +79991234567'
    except Exception as e:
        print(f"[ERROR] Phone parsing error: {e}")
        return None, 'Ошибка обработки номера телефона'


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Если уже авторизован
    if current_user.is_authenticated:
        flash('Вы уже авторизованы!', 'info')
        return redirect(url_for('index.index'))

    if request.method == 'POST':
        phone_raw = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        # Простая валидация
        if not phone_raw:
            flash('Введите номер телефона!', 'error')
            return render_template('login.html')

        if not password:
            flash('Введите пароль!', 'error')
            return render_template('login.html', phone=phone_raw)

        # Нормализация телефона
        phone_normalized, error_msg = normalize_phone_number(phone_raw)
        if error_msg:
            flash(error_msg, 'error')
            return render_template('login.html', phone=phone_raw)

        # Поиск пользователя
        user = User.query.filter_by(phone=phone_normalized).first()

        if not user:
            flash('Пользователь с таким номером не найден', 'error')
            return render_template('login.html', phone=phone_raw)

        # Проверка пароля
        if not check_password_hash(user.password, password):
            flash('Неверный пароль', 'error')
            return render_template('login.html', phone=phone_raw)

        # Успешный вход
        login_user(user, remember=True)
        flash('Вы успешно вошли в систему!', 'success')

        # Редирект
        if user.is_admin:
            return redirect(url_for('admin.admin_dashboard'))
        else:
            return redirect(url_for('index.index'))

    return render_template('login.html')


@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index.index'))


@user_bp.route('/register', methods=['GET', 'POST'])
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

        # Валидация
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

        # Проверка существования пользователя
        existing_user = User.query.filter_by(phone=phone_normalized).first()
        if existing_user:
            flash('Этот номер телефона уже зарегистрирован', 'error')
            return render_template('register.html',
                                   first_name=first_name,
                                   last_name=last_name,
                                   phone=phone_raw)

        try:
            # Создание пользователя
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            new_user = User(
                first_name=first_name,
                last_name=last_name,
                phone=phone_normalized,
                password=hashed_password
            )

            db.session.add(new_user)
            db.session.commit()

            # Автовход
            login_user(new_user, remember=True)

            flash('Регистрация успешна! Добро пожаловать!', 'success')
            return redirect(url_for('index.index'))

        except IntegrityError:
            db.session.rollback()
            flash('Ошибка при регистрации. Попробуйте позже.', 'error')
            return render_template('register.html',
                                   first_name=first_name,
                                   last_name=last_name,
                                   phone=phone_raw)
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Registration failed: {e}")
            flash('Произошла ошибка при регистрации.', 'error')
            return render_template('register.html',
                                   first_name=first_name,
                                   last_name=last_name,
                                   phone=phone_raw)

    return render_template('register.html')