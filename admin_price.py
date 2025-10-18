from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class PriceForm(FlaskForm):
    service_name = StringField('Название услуги', validators=[DataRequired()])
    description = TextAreaField('Описание')
    price = DecimalField('Цена (руб)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Сохранить')