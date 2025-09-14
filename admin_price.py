from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, DateField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed


class PriceForm(FlaskForm):
    service_name = StringField('Название услуги', validators=[DataRequired()])
    description = TextAreaField('Описание')
    price = DecimalField('Цена (руб)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Сохранить')