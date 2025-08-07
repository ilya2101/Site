from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash
import requests
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ilya'  # Нужен для flash-сообщений
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

print(type(db))


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')  # Страница "О нас"
def about():
    return render_template('about.html')  # или другая логика

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # Хеш пароля

# Создаем таблицы (выполнить один раз)
with app.app_context():
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Проверка паролей
        if password != confirm_password:
            flash('Пароли не совпадают!', 'danger')
            return redirect(url_for('register'))

        # Хешируем пароль
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Создаем пользователя
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=hashed_password
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('index'))
        except:
            db.session.rollback()
            flash('Ошибка: номер телефона уже занят', 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Ищем пользователя в БД
        user = User.query.filter_by(phone=phone).first()

        # Проверяем пароль
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Запоминаем пользователя
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный номер или пароль!', 'danger')

    return render_template('login.html')


@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('Сначала войдите в аккаунт!', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('account.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Удаляем user_id из сессии
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('index'))









if __name__ == '__main__':
    app.run(debug=True)
