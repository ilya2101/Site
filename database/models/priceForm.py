from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class PriceForm(FlaskForm):
    service_name = StringField('Название услуги', validators=[DataRequired()])
    description = TextAreaField('Описание')
    price = DecimalField('Цена', validators=[DataRequired(), NumberRange(min=0)])
    is_active = BooleanField('Активна', default=True)  # Добавьте это поле
    submit = SubmitField('Сохранить')