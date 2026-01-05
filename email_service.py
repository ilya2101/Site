# Стандартные библиотеки Python
import os
import logging
from datetime import datetime, timedelta  # для работы со временем

# Flask и расширения
from flask import current_app  # для доступа к конфигурации приложения
from flask_mail import Message  # для создания email сообщений

# Ваши собственные модули
from extensions import mail  # инициализированный объект Flask-Mail
from database.engine import db  # для работы с базой данных
from database.models import EmailAttempt  # новая модель для отслеживания попыток

logger = logging.getLogger(__name__)

def send_confirmation_email(user_email, confirmation_code, request=None):
    """
    Отправляет письмо с подтверждением email с проверкой лимитов
    """
    try:
        # ========== ШАГ 1: Получаем информацию о запросе ==========
        # request - это объект Flask request, который содержит информацию о клиенте
        ip_address = request.remote_addr if request else '127.0.0.1'  # IP адрес пользователя
        user_agent = request.user_agent.string if request else 'Unknown'  # Браузер/устройство

        # ========== ШАГ 2: Проверяем лимит по email (1 раз в 10 минут) ==========
        # Создаем временную метку "10 минут назад"
        ten_minutes_ago = datetime.utcnow() - datetime.timedelta(minutes=10)

        # Ищем в базе: все попытки отправки на этот email за последние 10 минут
        recent_attempts = EmailAttempt.query.filter(
            EmailAttempt.email == user_email,           # для этого email
            EmailAttempt.sent_at > ten_minutes_ago      # отправленные после "10 минут назад"
        ).count()  # считаем количество

        # Если уже была отправка за последние 10 минут - отклоняем
        if recent_attempts >= 1:
            logger.warning(f"❌ Превышен лимит отправок для {user_email}: {recent_attempts} попыток за 10 минут")

            # Возвращаем специальный результат вместо True/False
            return {
                'success': False,  # не удалось
                'message': 'Слишком частые запросы. Подождите 10 минут перед следующей отправкой.',
                'limit_type': 'email',  # тип ограничения
                'wait_minutes': 10      # сколько ждать
            }

        # ========== ШАГ 3: Проверяем лимит по IP (10 раз в 24 часа) ==========
        # Создаем временную метку "24 часа назад"
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)

        # Ищем в базе: все попытки отправки с этого IP за последние 24 часа
        ip_attempts = EmailAttempt.query.filter(
            EmailAttempt.ip_address == ip_address,      # для этого IP
            EmailAttempt.sent_at > twenty_four_hours_ago  # отправленные после "24 часа назад"
        ).count()  # считаем количество

        # Если больше 10 попыток за сутки - отклоняем
        if ip_attempts >= 10:
            logger.warning(f"❌ Превышен суточный лимит для IP {ip_address}: {ip_attempts} попыток")

            return {
                'success': False,
                'message': 'Превышен суточный лимит отправок с вашего устройства.',
                'limit_type': 'ip',
                'wait_hours': 24
            }

        # ========== ШАГ 4: Сохраняем информацию о попытке в БД ==========
        # Создаем новую запись в таблице EmailAttempt
        attempt = EmailAttempt(
            email=user_email,               # email пользователя
            ip_address=ip_address,          # его IP адрес
            user_agent=user_agent,          # информация о браузере
            confirmation_code=confirmation_code  # отправленный код (для логов)
        )

        # Добавляем запись в сессию БД (пока не сохраняем)
        db.session.add(attempt)

        # ========== ШАГ 5: Отправляем письмо (ваш существующий код) ==========
        # ВАЖНО: Используйте ваш реальный домен вместо 127.0.0.1:5000
        base_url = current_app.config.get('BASE_URL', 'http://127.0.0.1:5000')

        # Создаем ссылку для подтверждения напрямую
        confirm_url = f"{base_url}/service/confirm-email/{confirmation_code}"

        # Ссылка на страницу ввода кода вручную
        manual_confirm_url = f"{base_url}/service/confirm-email-page"

        # Создаем сообщение
        msg = Message(
            subject='✅ Подтверждение регистрации в ADRAuto',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@adrauto.ru'),
            recipients=[user_email]
        )

        # Текстовая версия (обновленная)
        msg.body = f'''Здравствуйте!

Спасибо за регистрацию в ADRAuto!

Для подтверждения вашего email перейдите по ссылке:
{confirm_url}

Или введите код подтверждения на странице: {manual_confirm_url}
Код: {confirmation_code}

Ссылка и код действительны 10 минут.

Если вы не регистрировались в ADRAuto, проигнорируйте это письмо.

С уважением,
Команда ADRAuto
'''

        # HTML версия (обновленная)
        msg.html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Подтверждение регистрации</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px;">
                <div style="text-align: center; background: linear-gradient(135deg, #FF6B35, #FF8C42); padding: 30px; border-radius: 10px 10px 0 0; color: white;">
                    <h1 style="margin: 0;">ADRAuto</h1>
                    <h2 style="margin: 10px 0 0;">Подтверждение регистрации</h2>
                </div>
                
                <div style="padding: 30px;">
                    <p>Здравствуйте!</p>
                    <p>Спасибо за регистрацию в ADRAuto. Для завершения регистрации подтвердите ваш email.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{confirm_url}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #FF6B35, #FF8C42); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                            Подтвердить автоматически
                        </a>
                    </div>
                    
                    <p>Или вы можете:</p>
                    
                    <div style="background-color: #f9f9f9; border-left: 4px solid #FF6B35; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0 0 10px;"><strong>Ввести код вручную:</strong></p>
                        <div style="background: linear-gradient(145deg, #2D2D2D, #3A3A3A); color: white; font-size: 24px; letter-spacing: 8px; padding: 20px; text-align: center; border-radius: 8px; margin: 10px 0; font-family: monospace; font-weight: bold;">
                            {confirmation_code}
                        </div>
                        <p style="margin: 10px 0 0;">
                            <a href="{manual_confirm_url}" style="color: #FF6B35; text-decoration: none;">
                                Перейти на страницу ввода кода →
                            </a>
                        </p>
                    </div>
                    
                    <div style="background-color: #fff8f4; border: 1px solid #ffe0cc; padding: 15px; border-radius: 8px; margin-top: 25px;">
                        <p style="margin: 0; color: #e55a00;">
                            <strong>⏰ Важно:</strong> Ссылка и код действительны <strong>10 минут</strong>.
                        </p>
                        <p style="margin: 5px 0 0; color: #666;">
                            Если вы не регистрировались в ADRAuto, игнорируйте это письмо.
                        </p>
                    </div>
                </div>
                
                <div style="border-top: 1px solid #eee; padding-top: 20px; text-align: center; color: #666; font-size: 12px;">
                    <p style="margin: 0;">С уважением, команда ADRAuto</p>
                    <p style="margin: 5px 0 0;">Это автоматическое письмо, не отвечайте на него</p>
                </div>
            </div>
        </body>
        </html>
        '''

        # Отправляем письмо
        mail.send(msg)

        # ========== ШАГ 6: Сохраняем попытку в БД ==========
        # Только после успешной отправки письма сохраняем запись
        db.session.commit()

        logger.info(f"✅ Письмо с подтверждением отправлено на {user_email}")

        # Возвращаем успешный результат
        return {
            'success': True,
            'message': 'Письмо отправлено'
        }

    except Exception as e:
        # ========== ШАГ 7: Обработка ошибок ==========
        # Если что-то пошло не так, откатываем изменения в БД
        db.session.rollback()

        logger.error(f"❌ Ошибка отправки email на {user_email}: {str(e)}")

        return {
            'success': False,
            'message': f'Ошибка отправки: {str(e)}'
        }