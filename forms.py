from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, DateField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed

class DiscountForm(FlaskForm):
    title = StringField('Название акции', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    image = FileField('Изображение', validators=[  # Исправлено: FileField вместо TextAreaField
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
    ])
    is_active = BooleanField('Активна', default=True)
    expires_at = DateField('Действует до', format='%Y-%m-%d')
