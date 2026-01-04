# /home/ilya/Site/email_service.py

import os
from flask import current_app, url_for
from flask_mail import Message
from extensions import mail
import logging

logger = logging.getLogger(__name__)

def send_confirmation_email(user_email, confirmation_code):
    """
    Отправляет письмо с подтверждением email
    """
    try:
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

        logger.info(f"✅ Письмо с подтверждением отправлено на {user_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка отправки email на {user_email}: {str(e)}")
        return False