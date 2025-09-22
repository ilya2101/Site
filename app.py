import os
from datetime import datetime
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint
from flask import abort
from flask_login import LoginManager, login_required
from flask_login import current_user
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from wtforms import BooleanField, DateField
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired

from admin_price import PriceForm
from database.engine import db
# Импорты моделей
from database.models.user import User
from forms import DiscountForm
from routes.admin_routes.admin_discounts import admin_discounts
from routes.admin_routes.dashboard import admin_bp
from routes.admin_routes.queue import queue_bp
from routes.admin_routes.requests import admin_required_bp
from routes.admin_routes.service import service_bp
from routes.admin_routes.price import price_bp
from routes.admin_routes.admin_discounts import admin_discounts_bp
from routes.users_routes.index import index_route
from routes.users_routes.login import user_bp

from database.models.application import Application
from database.models.completed_service import CompletedService
from database.models.discount import Discount
from database.models.inService import InService
from database.models.queue import Queue
from database.models.servicePrice import ServicePrice


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function










app = Flask(__name__)

app.register_blueprint(index_route)

app.register_blueprint(user_bp)

app.register_blueprint(admin_bp)

app.register_blueprint(admin_required_bp)

app.register_blueprint(queue_bp)

app.register_blueprint(service_bp)

app.register_blueprint(price_bp)

app.register_blueprint(admin_discounts_bp)









app.config['SECRET_KEY'] = 'ilya'













# Конфигурация БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'



app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# СОЗДАЕМ login_manager ПЕРЕД инициализацией
login_manager = LoginManager(app)
login_manager.login_view = 'user.login'  # Исправлено на 'user.login'

# Инициализация базы данных
db.init_app(app)
with app.app_context():
    # Создать все таблицы для всех моделей
    db.create_all()
    print("Все таблицы созданы!")

login_manager.init_app(app)






migrate = Migrate(app, db)








# Настройка загрузки файлов
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'xls', 'xlsx', 'csv'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Создаем папку для загрузок
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# Регистрируем Blueprint




# Создаем папки для загрузок
def create_upload_folders():
    folders = [
        'static/uploads/discounts',
        'static/uploads'
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Папка создана: {folder}")

create_upload_folders()

# Функция создания администратора
def create_admin():
    try:
        admin_phone = "+71234567890"
        admin_password = "secret123"

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin:
            hashed_password = generate_password_hash(admin_password)
            admin = User(
                first_name="Admin",
                last_name="Admin",
                phone=admin_phone,
                password=hashed_password,
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists!")
    except Exception as e:
        print(f"Error creating admin: {e}")

# Создаем администратора
with app.app_context():
    create_admin()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))












@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)



class ServiceRequest:
    pass














@app.route('/about')
def about():
    render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contact.html')

@app.route('/discounts')
def discounts():
    # Получаем только активные скидки
    active_discounts = Discount.query.filter(
        Discount.is_active == True,
        (Discount.expires_at.is_(None)) | (Discount.expires_at >= datetime.now())
    ).order_by(Discount.created_at.desc()).all()

    return render_template('discounts.html',
                           discounts=active_discounts,
                           user=current_user)  # Добавьте эту строку


@app.route('/price')
def price():
    # Если у вас есть модель ServicePrice
    active_prices = ServicePrice.query.filter_by(is_active=True).order_by(ServicePrice.service_name).all()
    return render_template('price.html', prices=active_prices)







# Найдите старую функцию price() и замените ее на эту:
@app.route('/price', endpoint='price_main')
def price():
    active_prices = ServicePrice.query.filter_by(is_active=True).order_by(ServicePrice.service_name).all()

    # Отладочная информация
    print(f"Найдено активных цен: {len(active_prices)}")
    for price in active_prices:
        print(f"Услуга: {price.service_name}, Цена: {price.price}")

    return render_template('price.html', prices=active_prices)

@app.route('/service-prices')  # Измените URL
def get_service_prices():        # Измените имя функции
    active_prices = ServicePrice.query.filter_by(is_active=True).order_by(ServicePrice.service_name).all()
    return render_template('price.html', prices=active_prices)






















































if __name__ == "__main__":
    app.run(debug=True)
