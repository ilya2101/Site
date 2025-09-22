from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField, FileField, BooleanField, DateField
from wtforms.validators import DataRequired


class DiscountForm(FlaskForm):
    __tablename__ = 'discountForm'
    title = StringField('Название акции', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    image = FileField('Изображение', validators=[  # Исправлено: FileField вместо TextAreaField
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
    ])
    is_active = BooleanField('Активна', default=True)
    expires_at = DateField('Действует до', format='%Y-%m-%d')