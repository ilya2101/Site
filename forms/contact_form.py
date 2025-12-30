from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField  # Добавь другие поля, если нужно
from wtforms.validators import DataRequired, ValidationError
import phonenumbers

# Кастомный валидатор для телефона
def validate_phone(form, field):
    if not field.data:  # Если поле пустое и необязательное — ок
        return

    try:
        parsed = phonenumbers.parse(field.data, "RU")  # "RU" для России, можно убрать или изменить
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError("Неверный номер телефона! Пример: +79991234567")
    except phonenumbers.NumberParseException:
        raise ValidationError("Введи нормальный номер телефона, без хуйни!")

# Сама форма (пример для обратной связи или заказа)
class ContactForm(FlaskForm):  # Или OrderForm, BookingForm — назови как тебе нужно
    name = StringField('Имя', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[DataRequired(), validate_phone])
    message = TextAreaField('Сообщение')  # Если нужно
    submit = SubmitField('Отправить')