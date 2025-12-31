# routes/auth_register.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, url_for
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
import re
from datetime import datetime, timedelta
import uuid

from database.engine import db
from database.models.user import User
from utils.phone_utils import normalize_phone_number

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
    Валидация email (только @mail @gmail @yandex @vk .com или .ru)
    Возвращает (email, сообщение_об_ошибке)
    """
    if not email:
        return None, 'Email обязателен для заполнения'

    email = email.strip().lower()

    # Проверяем общий формат email
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return None, 'Введите корректный email адрес'

    # Проверяем допустимые домены
    allowed_domains = ['mail.ru', 'gmail.com', 'yandex.ru', 'yandex.com', 'vk.com']
    domain = email.split('@')[1] if '@' in email else ''

    # Проверяем на соответствие допустимым доменам
    if not any(domain.endswith(allowed) for allowed in allowed_domains):
        return None, 'Допустимы только @mail.ru, @gmail.com, @yandex.ru, @vk.com'

    # Проверка на максимальную длину
    if len(email) > 50:
        return None, 'Email слишком длинный (максимум 50 символов)'

    return email, None


def validate_password(password):
    """
    Валидация пароля
    """
    if not password:
        return 'Введите пароль'

    if len(password) < 8:
        return 'Пароль должен быть не менее 8 символов'

    if len(password) > 50:
        return 'Пароль слишком длинный (максимум 50 символов)'

    if not re.search(r'[A-ZА-Я]', password):
        return 'Пароль должен содержать хотя бы одну заглавную букву'

    if not re.search(r'[a-zа-я]', password):
        return 'Пароль должен содержать хотя бы одну строчную букву'

    if not re.search(r'\d', password):
        return 'Пароль должен содержать хотя бы одну цифру'

    # Можно добавить проверку на специальные символы
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return 'Пароль должен содержать хотя бы один специальный символ (!@#$%^&* и т.д.)'

    return None


@register_bp.route('/register', methods=['GET', 'POST'])
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

        try:
            # Проверяем есть ли уже такой телефон в базе
            print(f"🔍 [DEBUG] Проверяем наличие телефона в базе...")
            existing_phone = User.query.filter_by(phone=validated_data['phone']).first()
            if existing_phone:
                print(f"⚠️ [DEBUG] Телефон уже существует в базе!")
                print(f"   ID пользователя: {existing_phone.id}")
                print(f"   Имя: {existing_phone.first_name} {existing_phone.last_name}")
                print(f"   Email: {existing_phone.email}")
            else:
                print(f"✅ [DEBUG] Телефон свободен")

            # Проверяем есть ли уже такой email в базе
            print(f"🔍 [DEBUG] Проверяем наличие email в базе...")
            existing_email = User.query.filter_by(email=validated_data['email']).first()
            if existing_email:
                print(f"⚠️ [DEBUG] Email уже существует в базе!")
                print(f"   ID пользователя: {existing_email.id}")
                print(f"   Имя: {existing_email.first_name} {existing_email.last_name}")
                print(f"   Телефон: {existing_email.phone}")
            else:
                print(f"✅ [DEBUG] Email свободен")

            # Хэшируем пароль
            print(f"🔍 [DEBUG] Хэшируем пароль...")
            hashed_password = generate_password_hash(
                validated_data['password'],
                method='pbkdf2:sha256'
            )
            print(f"✅ [DEBUG] Пароль захеширован")

            # Генерируем код подтверждения email
            email_confirmation_code = str(uuid.uuid4())[:8].upper()
            print(f"✅ [DEBUG] Код подтверждения: {email_confirmation_code}")

            # Создаем нового пользователя
            print(f"🔍 [DEBUG] Создаем объект пользователя...")
            new_user = User(
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                phone=validated_data['phone'],
                email=validated_data['email'],
                password=hashed_password,
                is_admin=False,
                email_confirmed=False,
                email_confirmation_code=email_confirmation_code,
                confirmation_sent_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            print(f"✅ [DEBUG] Объект пользователя создан")

            print(f"🔍 [DEBUG] Добавляем в сессию...")
            db.session.add(new_user)

            print(f"🔍 [DEBUG] Пытаемся сохранить в БД...")
            db.session.commit()
            print(f"🎉 [DEBUG] ПОЛЬЗОВАТЕЛЬ УСПЕШНО СОЗДАН!")
            print(f"   ID: {new_user.id}")
            print(f"   Телефон: {new_user.phone}")
            print(f"   Email: {new_user.email}")

            # Отправляем письмо с подтверждением
            print(f"🔍 [DEBUG] Пытаемся отправить письмо...")
            from email_service import send_confirmation_email
            email_sent = send_confirmation_email(new_user.email, email_confirmation_code)

            if email_sent:
                print(f"✅ [DEBUG] Письмо отправлено")
                flash('✅ Регистрация успешна! Проверьте вашу почту для подтверждения email.', 'success')
            else:
                print(f"⚠️ [DEBUG] Не удалось отправить письмо")
                flash('⚠️ Регистрация успешна, но не удалось отправить письмо подтверждения.', 'warning')

            return redirect(url_for('index.index'))

        except IntegrityError as e:
            db.session.rollback()
            print(f"❌ [DEBUG] IntegrityError при регистрации!")
            print(f"   Текст ошибки: {e}")
            print(f"   Тип ошибки: {type(e)}")
            print(f"   Аргументы: {e.args}")

            error_str = str(e).lower()
            print(f"   Ошибка в нижнем регистре: '{error_str}'")

            # Проверяем что это за ошибка
            if 'phone' in error_str:
                print(f"   ❌ Это ошибка телефона (дубликат)")
                flash('Этот номер телефона уже зарегистрирован', 'error')
                errors['phone'] = 'Этот номер телефона уже зарегистрирован'
            elif 'email' in error_str:
                print(f"   ❌ Это ошибка email (дубликат)")
                flash('Этот email уже зарегистрирован', 'error')
                errors['email'] = 'Этот email уже зарегистрирован'
            else:
                print(f"   ❌ Неизвестная IntegrityError")
                flash('Ошибка при регистрации', 'error')

        except Exception as e:
            db.session.rollback()
            print(f"❌ [DEBUG] Общая ошибка при регистрации!")
            print(f"   Тип: {type(e)}")
            print(f"   Сообщение: {str(e)}")
            import traceback
            traceback.print_exc()

            current_app.logger.error(f"Неожиданная ошибка при регистрации: {e}")
            flash('Произошла неожиданная ошибка при регистрации.', 'error')

        # Если что-то пошло не так — возвращаем форму с сохраненными данными
        print(f"🔍 [DEBUG] Возвращаем форму с ошибками: {errors}")
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
def confirm_email(confirmation_code):
    """
    Подтверждение email по коду из письма
    """
    # Ищем пользователя по коду
    user = User.query.filter_by(email_confirmation_code=confirmation_code).first()

    if not user:
        flash('Неверный код подтверждения', 'error')
        return redirect(url_for('index.index'))

    # Проверяем не истек ли срок действия кода (24 часа)
    if user.confirmation_sent_at:
        expiration_time = user.confirmation_sent_at + timedelta(hours=24)
        if datetime.utcnow() > expiration_time:
            flash('Срок действия кода подтверждения истек', 'error')
            return redirect(url_for('index.index'))

    # Если email уже подтвержден
    if user.email_confirmed:
        flash('Ваш email уже подтвержден', 'info')
    else:
        # Подтверждаем email
        user.email_confirmed = True
        user.email_confirmation_code = None
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
    from email_service import send_confirmation_email
    email_sent = send_confirmation_email(current_user.email, new_code)

    if email_sent:
        flash('✅ Новое письмо с подтверждением отправлено на вашу почту', 'success')
    else:
        flash('❌ Не удалось отправить письмо. Попробуйте позже.', 'error')

    return redirect(url_for('index.index'))