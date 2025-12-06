import os

from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask import abort
from flask_login import LoginManager, login_required
from flask_login import current_user
from flask_migrate import Migrate

from database.engine import db
from database.models.servicePrice import ServicePrice
from database.models.user import User
from routes.admin_routes.admin_discounts import admin_discounts_bp
from routes.admin_routes.dashboard import admin_bp
from routes.admin_routes.price import price_bp
from routes.admin_routes.queue import queue_bp
from routes.admin_routes.requests import admin_required_bp
from routes.admin_routes.service import service_bp
from routes.admin_routes.visit import visit_bp, log_visit
from routes.users_routes.index import index_route
from routes.users_routes.login import user_bp

from mobile_routes.mob_db import mob_db  # ← ИСПРАВЛЕННЫЙ ИМПОРТ
from flask_cors import CORS

load_dotenv()

app = Flask(__name__, static_url_path="/service/static", static_folder="static")
CORS(app)

# Конфигурация
app.config['SECRET_KEY'] = 'ilya'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Инициализация БД
db.init_app(app)

# Миграции
migrate = Migrate(app, db)

# Login manager
login_manager = LoginManager(app)
login_manager.login_view = 'user.login'

# Регистрация mobile blueprint ПЕРВЫМ
app.register_blueprint(mob_db)  # ← Теперь mob_db это Blueprint

# Регистрация остальных blueprints
blueprints = [
    index_route,
    user_bp,
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

# Остальной код без изменений...
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

# Создаем папку для загрузок
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def create_upload_folders():
    folders = [
        'static/uploads/discounts',
        'static/uploads'
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Папка создана: {folder}")

create_upload_folders()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)

@app.route('/service-prices')
def get_service_prices():
    active_prices = ServicePrice.query.filter_by(is_active=True).order_by(ServicePrice.service_name).all()
    return render_template('price.html', prices=active_prices)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)

