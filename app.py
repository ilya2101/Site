# app.py

import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, render_template, abort
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from flask_cors import CORS

from database.engine import db
from database.models.user import User
from database.models.servicePrice import ServicePrice

# Импортируем блюпринты
from routes.users_routes.index import index_route
from routes.users_routes.login import user_bp
from routes.users_routes.auth_register import register_bp# или как ты назвал
from routes.admin_routes.dashboard import admin_bp
from routes.admin_routes.requests import admin_required_bp
from routes.admin_routes.queue import queue_bp
from routes.admin_routes.service import service_bp
from routes.admin_routes.price import price_bp
from routes.admin_routes.admin_discounts import admin_discounts_bp
from routes.admin_routes.visit import visit_bp
from mobile_routes.mob_db import mob_db

load_dotenv()

# Создаём приложение
app = Flask(__name__, static_url_path="/service/static", static_folder="static")
CORS(app)

# Конфигурация
app.config['SECRET_KEY'] = 'ilya'  # ОБЯЗАТЕЛЬНО смени в продакшене!
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Инициализация расширений
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'user_bp.login'  # важно: имя_блюпринта.имя_функции

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Регистрация блюпринтов (ТОЛЬКО ПОСЛЕ создания app!)

# Сначала мобильный API (без префикса, если нужно)
app.register_blueprint(mob_db)

# Затем основные маршруты с префиксом /service
blueprints = [
    index_route,
    user_bp,              # login + logout
    register_bp,     # регистрация — убедись, что имя импорта правильное!
    admin_bp,
    admin_required_bp,
    queue_bp,
    service_bp,
    price_bp,
    admin_discounts_bp,
    visit_bp,
]

for bp in blueprints:
    app.register_blueprint(bp, url_prefix="/service")

# Декоратор админа
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Настройка загрузки файлов
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'xls', 'xlsx', 'csv'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Создание папок
def create_upload_folders():
    folders = [
        'static/uploads/discounts',
        'static/uploads'
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Папка создана: {folder}")

create_upload_folders()

# Обычные маршруты
@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)

@app.route('/service-prices')
def get_service_prices():
    active_prices = ServicePrice.query.filter_by(is_active=True).order_by(ServicePrice.service_name).all()
    return render_template('price.html', prices=active_prices)

# Запуск
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)