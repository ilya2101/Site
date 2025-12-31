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
        # Создаем ссылку для подтверждения
        confirm_url = url_for('register.confirm_email',
                              confirmation_code=confirmation_code,
                              _external=True)

        # Создаем сообщение
        msg = Message(
            subject='✅ Подтверждение регистрации в ADRAuto',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@adrauto.ru'),
            recipients=[user_email]
        )

        # Текстовая версия (простой текст)
        msg.body = f'''Здравствуйте!

Спасибо за регистрацию в ADRAuto!

Для подтверждения вашего email перейдите по ссылке:
{confirm_url}

Или введите код подтверждения на сайте: {confirmation_code}

Ссылка действительна 24 часа.

Если вы не регистрировались в ADRAuto, проигнорируйте это письмо.

С уважением,
Команда ADRAuto
'''

        # HTML версия (красивая)
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
                            Подтвердить email
                        </a>
                    </div>
                    
                    <p style="text-align: center;">Или введите этот код на сайте:</p>
                    
                    <div style="background: linear-gradient(145deg, #2D2D2D, #3A3A3A); color: white; font-size: 24px; letter-spacing: 8px; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; font-family: monospace; font-weight: bold;">
                        {confirmation_code}
                    </div>
                    
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin-top: 25px;">
                        <p style="margin: 0; color: #666;">
                            <strong>Важно:</strong> Ссылка и код действительны 24 часа.
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