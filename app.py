from functools import wraps

from flask import Flask, render_template, request
from flask import abort
from flask_login import LoginManager, login_required
from flask_login import current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash

from database.engine import db
from database.models.servicePrice import ServicePrice
# Импорты моделей
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

app = Flask(__name__)

app.register_blueprint(index_route)

app.register_blueprint(user_bp)

app.register_blueprint(admin_bp)

app.register_blueprint(admin_required_bp)

app.register_blueprint(queue_bp)

app.register_blueprint(service_bp)

app.register_blueprint(price_bp)

app.register_blueprint(admin_discounts_bp)

app.register_blueprint(visit_bp)




def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function





import os

print("STATIC FOLDER:", os.path.join(os.getcwd(), "static", "img", "photo_for_about", "Chatgpt_mexanic.jpg"))
print("EXISTS:", os.path.exists(os.path.join(os.getcwd(), "static", "img", "photo_for_about", "Chatgpt_mexanic.jpg")))








app.config['SECRET_KEY'] = 'ilya'

# Конфигурация PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Дополнительные настройки (опционально)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}
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

def track_visits():
    # Исключаем статические файлы и админские страницы, если нужно
    if request.endpoint and not request.endpoint.startswith('static'):
        log_visit()

import os


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))



@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)



class ServiceRequest:
    pass



@app.route('/service-prices')  # Измените URL
def get_service_prices():        # Измените имя функции
    active_prices = ServicePrice.query.filter_by(is_active=True).order_by(ServicePrice.service_name).all()
    return render_template('price.html', prices=active_prices)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)