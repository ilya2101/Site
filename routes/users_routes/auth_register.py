# routes/auth_register.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
import re
from datetime import datetime, timedelta
import uuid

from database.engine import db
from database.models import EmailAttempt
from database.models.user import User
from utils.phone_utils import normalize_phone_number
from email_service import send_confirmation_email  # Импорт ВНЕРТИ функции!

# Создаём блюпринт
register_bp = Blueprint('register', __name__)


def validate_russian_name(name, field_name):
    """
    Валидация русского имени/фамилии
    Возвращает (очищенное_имя, сообщение_об_ошибке)
    """
    if not name:
        return None, f'{field_name} обязательно для заполнения'

    name = name.strip()

    # Проверка ТОЛЬКО на русские буквы (без пробелов, дефисов и других символов)
    if not re.match(r'^[А-Яа-яЁё]+$', name):
        return None, f'{field_name} должно содержать только русские буквы'

    # Минимальная и максимальная длина
    if len(name) < 2:
        return None, f'{field_name} должно быть не менее 2 символов'
    if len(name) > 30:
        return None, f'{field_name} должно быть не более 30 символов'

    # Приводим к формату: первая буква заглавная, остальные строчные
    normalized_name = name.capitalize()
    return normalized_name, None


def validate_phone(phone_raw):
    """
    Валидация номера телефона (только цифры, российский формат)
    """
    print(f"🔍 [validate_phone] Вход: '{phone_raw}'")

    if not phone_raw:
        print(f"❌ [validate_phone] Пустой номер")
        return None, 'Введите номер телефона'

    # Удаляем все символы кроме цифр
    phone_digits = re.sub(r'\D', '', phone_raw)
    print(f"🔍 [validate_phone] Только цифры: '{phone_digits}'")

    # Проверяем длину (без кода страны +7 это 10 цифр)
    if len(phone_digits) != 11:
        print(f"❌ [validate_phone] Неправильная длина: {len(phone_digits)} (должно быть 11)")
        return None, 'Номер телефона должен содержать 11 цифр (включая +7)'

    # Проверяем, что номер начинается с 7 или 8 (российский код)
    if not phone_digits.startswith(('7', '8')):
        print(f"❌ [validate_phone] Не начинается с 7 или 8: '{phone_digits[0]}'")
        return None, 'Номер должен начинаться с +7'

    # Форматируем в стандартный формат +7XXXXXXXXXX
    if phone_digits.startswith('8'):
        phone_digits = '7' + phone_digits[1:]
        print(f"🔄 [validate_phone] Исправляем 8 на 7: '{phone_digits}'")

    phone_normalized = f'+7{phone_digits[1:]}'
    print(f"✅ [validate_phone] Нормализованный: '{phone_normalized}'")
    return phone_normalized, None


def validate_email(email):
    """
    Валидация email (упрощенная версия)
    Возвращает (email, сообщение_об_ошибке)
    """
    if not email:
        return None, 'Email обязателен для заполнения'

    email = email.strip().lower()

    # Упрощенная проверка email
    if '@' not in email or '.' not in email:
        return None, 'Введите корректный email адрес'

    # Разделяем email на локальную часть и домен
    local_part, domain = email.split('@', 1)

    # Проверяем минимальную длину
    if len(local_part) < 1:
        return None, 'Некорректный email адрес'

    # Проверка на максимальную длину
    if len(email) > 50:
        return None, 'Email слишком длинный (максимум 50 символов)'

    return email, None


def validate_password(password):
    """
    Валидация пароля (упрощенная версия)
    """
    if not password:
        return 'Введите пароль'

    if len(password) < 8:
        return 'Пароль должен быть не менее 8 символов'

    if len(password) > 50:
        return 'Пароль слишком длинный (максимум 50 символов)'

    # Базовые проверки (можно закомментировать для тестирования)
    if not re.search(r'[A-ZА-Я]', password):
        return 'Пароль должен содержать хотя бы одну заглавную букву'

    if not re.search(r'[a-zа-я]', password):
        return 'Пароль должен содержать хотя бы одну строчную букву'

    if not re.search(r'\d', password):
        return 'Пароль должен содержать хотя бы одну цифру'

    return None


# Добавляем в импорты:
from flask import session

# Изменяем функцию register() после валидации данных:




@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Вы уже авторизованы!', 'info')
        return redirect(url_for('index.index'))

    if request.method == 'POST':
        # Получаем данные из формы
        first_name_raw = request.form.get('first_name', '').strip()
        last_name_raw = request.form.get('last_name', '').strip()
        phone_raw = request.form.get('phone', '').strip()
        email_raw = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        agree_terms = request.form.get('agree_terms')

        print(f"\n🔍 [DEBUG] ===== НАЧАЛО РЕГИСТРАЦИИ =====")
        print(f"🔍 [DEBUG] Имя: '{first_name_raw}'")
        print(f"🔍 [DEBUG] Фамилия: '{last_name_raw}'")
        print(f"🔍 [DEBUG] Телефон (сырой): '{phone_raw}'")
        print(f"🔍 [DEBUG] Email: '{email_raw}'")
        print(f"🔍 [DEBUG] Пароль: {'*' * len(password)}")
        print(f"🔍 [DEBUG] Подтверждение пароля: {'*' * len(confirm_password)}")
        print(f"🔍 [DEBUG] Согласие с условиями: {bool(agree_terms)}")

        # Храним ошибки для отображения пользователю
        errors = {}
        validated_data = {}

        # Валидация имени
        print(f"🔍 [DEBUG] --- Валидация имени ---")
        first_name, first_name_error = validate_russian_name(first_name_raw, 'Имя')
        if first_name_error:
            print(f"❌ [DEBUG] Ошибка имени: {first_name_error}")
            errors['first_name'] = first_name_error
        else:
            print(f"✅ [DEBUG] Имя валидно: '{first_name}'")
            validated_data['first_name'] = first_name

        # Валидация фамилии
        print(f"🔍 [DEBUG] --- Валидация фамилии ---")
        last_name, last_name_error = validate_russian_name(last_name_raw, 'Фамилия')
        if last_name_error:
            print(f"❌ [DEBUG] Ошибка фамилии: {last_name_error}")
            errors['last_name'] = last_name_error
        else:
            print(f"✅ [DEBUG] Фамилия валидна: '{last_name}'")
            validated_data['last_name'] = last_name

        # Валидация телефона
        print(f"🔍 [DEBUG] --- Валидация телефона ---")
        phone_normalized, phone_error = validate_phone(phone_raw)
        if phone_error:
            print(f"❌ [DEBUG] Ошибка телефона: {phone_error}")
            errors['phone'] = phone_error
        else:
            print(f"✅ [DEBUG] Телефон валиден: '{phone_normalized}'")
            validated_data['phone'] = phone_normalized

        # Валидация email
        print(f"🔍 [DEBUG] --- Валидация email ---")
        email, email_error = validate_email(email_raw)
        if email_error:
            print(f"❌ [DEBUG] Ошибка email: {email_error}")
            errors['email'] = email_error
        else:
            print(f"✅ [DEBUG] Email валиден: '{email}'")
            validated_data['email'] = email

        # Валидация пароля
        print(f"🔍 [DEBUG] --- Валидация пароля ---")
        password_error = validate_password(password)
        if password_error:
            print(f"❌ [DEBUG] Ошибка пароля: {password_error}")
            errors['password'] = password_error
        elif password != confirm_password:
            print(f"❌ [DEBUG] Пароли не совпадают")
            errors['confirm_password'] = 'Пароли не совпадают'
        else:
            print(f"✅ [DEBUG] Пароль валиден")
            validated_data['password'] = password

        # Проверка согласия с условиями
        if not agree_terms:
            print(f"❌ [DEBUG] Нет согласия с условиями")
            errors['agree_terms'] = 'Необходимо согласиться с условиями использования'

        # Если есть ошибки, показываем их пользователю
        if errors:
            print(f"🚫 [DEBUG] Есть ошибки валидации: {errors}")
            for field, error_message in errors.items():
                flash(f'{error_message}', 'error')

            return render_template('register.html',
                                   first_name=first_name_raw,
                                   last_name=last_name_raw,
                                   phone=phone_raw,
                                   email=email_raw,
                                   errors=errors)

        print(f"✅ [DEBUG] Все данные валидны!")
        print(f"📋 [DEBUG] Валидированные данные:")
        print(f"  👤 Имя: {validated_data['first_name']}")
        print(f"  👤 Фамилия: {validated_data['last_name']}")
        print(f"  📱 Телефон: {validated_data['phone']}")
        print(f"  📧 Email: {validated_data['email']}")
        print(f"  🔐 Пароль (хеш): будет сгенерирован")

        # ТЕПЕРЬ блок try-except идет ЗДЕСЬ, после проверки ошибок
        try:
            # 1. Проверяем дубликаты
            print(f"🔍 [DEBUG] Проверяем наличие телефона в базе...")
            existing_phone = User.query.filter_by(phone=validated_data['phone']).first()
            if existing_phone:
                print(f"⚠️ [DEBUG] Телефон уже существует в базе!")
                flash('Этот номер телефона уже зарегистрирован', 'error')
                errors['phone'] = 'Этот номер телефона уже зарегистрирован'
                return render_template('register.html',
                                       first_name=first_name_raw,
                                       last_name=last_name_raw,
                                       phone=phone_raw,
                                       email=email_raw,
                                       errors=errors)
            else:
                print(f"✅ [DEBUG] Телефон свободен")

            print(f"🔍 [DEBUG] Проверяем наличие email в базе...")
            existing_email = User.query.filter_by(email=validated_data['email']).first()
            if existing_email:
                print(f"⚠️ [DEBUG] Email уже существует в базе!")
                flash('Этот email уже зарегистрирован', 'error')
                errors['email'] = 'Этот email уже зарегистрирован'
                return render_template('register.html',
                                       first_name=first_name_raw,
                                       last_name=last_name_raw,
                                       phone=phone_raw,
                                       email=email_raw,
                                       errors=errors)
            else:
                print(f"✅ [DEBUG] Email свободен")

            # 2. Хэшируем пароль
            print(f"🔍 [DEBUG] Хэшируем пароль...")
            hashed_password = generate_password_hash(
                validated_data['password'],
                method='pbkdf2:sha256'
            )
            print(f"✅ [DEBUG] Пароль захеширован")

            # 3. Генерируем код подтверждения
            email_confirmation_code = str(uuid.uuid4())[:8].upper()
            print(f"✅ [DEBUG] Код подтверждения: {email_confirmation_code}")

            # 4. Сохраняем данные в сессии (НЕ в БД!)
            session['registration_data'] = {
                'first_name': validated_data['first_name'],
                'last_name': validated_data['last_name'],
                'phone': validated_data['phone'],
                'email': validated_data['email'],
                'password_hash': hashed_password,
                'confirmation_code': email_confirmation_code,
                'confirmation_sent_at': datetime.utcnow().isoformat()
            }

            # Устанавливаем срок жизни сессии (например, 1 час)
            session.permanent = True

            # 5. Отправляем письмо
            print(f"🔍 [DEBUG] Пытаемся отправить письмо...")
            email_sent = send_confirmation_email(validated_data['email'], email_confirmation_code)

            if not email_sent:
                print(f"❌ [DEBUG] Не удалось отправить письмо")
                # Очищаем сессию при ошибке
                session.pop('registration_data', None)
                flash('❌ Не удалось отправить письмо с подтверждением. Попробуйте позже.', 'error')
                return render_template('register.html',
                                       first_name=first_name_raw,
                                       last_name=last_name_raw,
                                       phone=phone_raw,
                                       email=email_raw,
                                       errors=errors)

            print(f"✅ [DEBUG] Письмо отправлено")

            # 6. Перенаправляем на страницу подтверждения
            flash('📧 На вашу почту отправлен код подтверждения. Введите его ниже.', 'info')
            return redirect(url_for('register.confirm_email_page'))

        except Exception as e:
            print(f"❌ [DEBUG] Ошибка при регистрации!")
            print(f"   Тип: {type(e)}")
            print(f"   Сообщение: {str(e)}")
            import traceback
            traceback.print_exc()

            # Очищаем сессию при ошибке
            session.pop('registration_data', None)
            current_app.logger.error(f"Ошибка при регистрации: {e}")
            flash('Произошла неожиданная ошибка при регистрации.', 'error')

            return render_template('register.html',
                                   first_name=first_name_raw,
                                   last_name=last_name_raw,
                                   phone=phone_raw,
                                   email=email_raw,
                                   errors=errors)

    # GET-запрос
    print(f"🔍 [DEBUG] GET-запрос на регистрацию")
    return render_template('register.html')






# Дополнительный маршрут для подтверждения email
@register_bp.route('/confirm-email/<confirmation_code>')
def confirm_email_by_link(confirmation_code):
    """
    Подтверждение email по коду из письма
    """
    # Ищем пользователя по коду
    user = User.query.filter_by(email_confirmation_code=confirmation_code).first()

    if not user:
        flash('Неверный код подтверждения', 'error')
        return redirect(url_for('index.index'))

    # Проверяем не истек ли срок действия кода (10 минут вместо 24 часов)
    if user.confirmation_sent_at:
        expiration_time = user.confirmation_sent_at + timedelta(minutes=10)  # Изменено здесь
        if datetime.utcnow() > expiration_time:
            # Автоматически генерируем новый код при истечении времени
            flash('Срок действия кода подтверждения истек (10 минут). Пожалуйста, запросите новый код.', 'error')

            # Удаляем старый просроченный код
            user.email_confirmation_code = None
            db.session.commit()

            # Перенаправляем на страницу входа с предложением запросить новый код
            return redirect(url_for('user.login'))

    # Если email уже подтвержден
    if user.email_confirmed:
        flash('Ваш email уже подтвержден', 'info')
    else:
        # Подтверждаем email
        user.email_confirmed = True
        user.email_confirmation_code = None
        user.email_confirmed_at = datetime.utcnow()  # Добавляем время подтверждения
        db.session.commit()

        flash('✅ Ваш email успешно подтвержден! Теперь вы можете войти в аккаунт.', 'success')

    # Перенаправляем на страницу входа
    return redirect(url_for('user.login'))



# Маршрут для повторной отправки подтверждения
@register_bp.route('/resend-confirmation')
def resend_confirmation():
    """
    Повторная отправка письма с подтверждением
    """
    if not current_user.is_authenticated:
        flash('Сначала войдите в аккаунт', 'error')
        return redirect(url_for('user.login'))

    if current_user.email_confirmed:
        flash('Ваш email уже подтвержден', 'info')
        return redirect(url_for('index.index'))

    # Генерируем новый код
    new_code = str(uuid.uuid4())[:8].upper()
    current_user.email_confirmation_code = new_code
    current_user.confirmation_sent_at = datetime.utcnow()
    db.session.commit()

    # Отправляем письмо
    try:
        email_sent = send_confirmation_email(current_user.email, new_code)

        if email_sent:
            flash('✅ Новое письмо с подтверждением отправлено на вашу почту', 'success')
        else:
            flash('❌ Не удалось отправить письмо. Попробуйте позже.', 'error')
    except Exception as e:
        flash('❌ Ошибка при отправке письма', 'error')

    return redirect(url_for('index.index'))




@register_bp.route('/confirm-email-page', methods=['GET', 'POST'])
def confirm_email_page():
    """
    Страница для ввода кода подтверждения
    """
    # Проверяем есть ли данные в сессии
    if 'registration_data' not in session:
        flash('❌ Сессия истекла или данные не найдены. Пожалуйста, начните регистрацию заново.', 'error')
        return redirect(url_for('register.register'))

    if request.method == 'POST':
        # Получаем код из формы
        entered_code = request.form.get('confirmation_code', '').strip().upper()

        # Получаем данные из сессии
        reg_data = session.get('registration_data')
        expected_code = reg_data.get('confirmation_code')
        confirmation_sent_at_str = reg_data.get('confirmation_sent_at')

        # Проверяем срок действия кода (10 минут)
        if confirmation_sent_at_str:
            confirmation_sent_at = datetime.fromisoformat(confirmation_sent_at_str)
            expiration_time = confirmation_sent_at + timedelta(minutes=10)
            if datetime.utcnow() > expiration_time:
                flash('⏰ Срок действия кода истек (10 минут). Пожалуйста, запросите новый код.', 'error')
                return redirect(url_for('register.resend_confirmation_code'))

        # Проверяем код
        if not entered_code:
            flash('❌ Введите код подтверждения', 'error')
            return render_template('confirm_email.html',
                                   email=reg_data.get('email', ''),
                                   expires_in_seconds=calculate_time_left(confirmation_sent_at_str))

        if entered_code != expected_code:
            flash('❌ Неверный код подтверждения. Попробуйте еще раз.', 'error')
            return render_template('confirm_email.html',
                                   email=reg_data.get('email', ''),
                                   expires_in_seconds=calculate_time_left(confirmation_sent_at_str))

        # Проверяем дубликаты перед созданием
        existing_user = User.query.filter(
            (User.phone == reg_data['phone']) |
            (User.email == reg_data['email'])
        ).first()

        if existing_user:
            # Очищаем сессию
            session.pop('registration_data', None)

            if existing_user.phone == reg_data['phone']:
                flash('❌ Этот номер телефона уже зарегистрирован', 'error')
            else:
                flash('❌ Этот email уже зарегистрирован', 'error')
            return redirect(url_for('register.register'))

        # Код верный - создаем пользователя
        try:
            new_user = User(
                first_name=reg_data['first_name'],
                last_name=reg_data['last_name'],
                phone=reg_data['phone'],
                email=reg_data['email'],
                password=reg_data['password_hash'],
                is_admin=False,
                email_confirmed=True,
                email_confirmation_code=None,
                confirmation_sent_at=datetime.fromisoformat(confirmation_sent_at_str) if confirmation_sent_at_str else None,
                created_at=datetime.utcnow()
            )

            db.session.add(new_user)
            db.session.commit()

            print(f"🎉 [DEBUG] ПОЛЬЗОВАТЕЛЬ УСПЕШНО СОЗДАН! ID: {new_user.id}")

            # Очищаем сессию
            session.pop('registration_data', None)

            # Логиним пользователя
            login_user(new_user, remember=False)

            flash('🎉 Регистрация успешно завершена! Добро пожаловать в ADRAuto!', 'success')
            return redirect(url_for('index.index'))

        except IntegrityError as e:
            db.session.rollback()
            if 'phone' in str(e).lower():
                flash('❌ Этот номер телефона уже зарегистрирован', 'error')
            elif 'email' in str(e).lower():
                flash('❌ Этот email уже зарегистрирован', 'error')
            else:
                flash('❌ Ошибка при регистрации. Попробуйте еще раз.', 'error')
            current_app.logger.error(f"Ошибка IntegrityError: {e}")
            return render_template('confirm_email.html',
                                   email=reg_data.get('email', ''),
                                   expires_in_seconds=calculate_time_left(confirmation_sent_at_str))

        except Exception as e:
            db.session.rollback()
            print(f"❌ [DEBUG] Ошибка при создании пользователя: {e}")
            current_app.logger.error(f"Ошибка при создании пользователя: {e}")
            flash('❌ Внутренняя ошибка сервера. Попробуйте позже.', 'error')
            return render_template('confirm_email.html',
                                   email=reg_data.get('email', ''),
                                   expires_in_seconds=calculate_time_left(confirmation_sent_at_str))

    # GET-запрос - показываем форму ввода кода
    reg_data = session.get('registration_data', {})
    email = reg_data.get('email', '')
    confirmation_sent_at_str = reg_data.get('confirmation_sent_at')

    # Рассчитываем оставшееся время
    expires_in_seconds = calculate_time_left(confirmation_sent_at_str)

    return render_template('confirm_email.html',
                           email=email,
                           expires_in_seconds=expires_in_seconds)


def calculate_time_left(confirmation_sent_at_str):
    """
    Рассчитывает оставшееся время в секундах
    """
    if not confirmation_sent_at_str:
        return 600  # 10 минут по умолчанию

    try:
        confirmation_sent_at = datetime.fromisoformat(confirmation_sent_at_str)
        expiration_time = confirmation_sent_at + timedelta(minutes=10)
        time_left = max(0, int((expiration_time - datetime.utcnow()).total_seconds()))
        return time_left
    except Exception as e:
        current_app.logger.error(f"Ошибка расчета времени: {e}")
        return 600  # 10 минут по умолчанию













@register_bp.route('/resend-confirmation-code')
def resend_confirmation_code():
    """
    Повторная отправка кода подтверждения
    """
    if 'registration_data' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Сессия истекла'}), 400
        flash('❌ Сессия истекла. Пожалуйста, начните регистрацию заново.', 'error')
        return redirect(url_for('register.register'))

    reg_data = session.get('registration_data')
    email = reg_data.get('email')

    # Генерируем новый код
    new_code = str(uuid.uuid4())[:8].upper()

    # Обновляем данные в сессии с текущим временем
    reg_data['confirmation_code'] = new_code
    reg_data['confirmation_sent_at'] = datetime.utcnow().isoformat()
    session['registration_data'] = reg_data
    session.modified = True

    # Отправляем письмо
    email_sent = send_confirmation_email(email, new_code)

    if email_sent:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Новый код отправлен'})
        flash('✅ Новый код подтверждения отправлен на вашу почту', 'success')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Ошибка отправки'}), 500
        flash('❌ Не удалось отправить код. Попробуйте позже.', 'error')

    return redirect(url_for('register.confirm_email_page'))