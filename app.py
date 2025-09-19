import os
from datetime import datetime
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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
from routes.admin_routes.dashboard import admin_bp
from routes.admin_routes.queue import queue_bp
from routes.admin_routes.requests import admin_required_bp
from routes.admin_routes.service import service_bp
from routes.users_routes.index import index_route
from routes.users_routes.login import user_bp


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


app.config['SECRET_KEY'] = 'ilya'













# Конфигурация БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_BINDS'] = {
    'applications': 'sqlite:///applications.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# СОЗДАЕМ login_manager ПЕРЕД инициализацией
login_manager = LoginManager(app)
login_manager.login_view = 'user.login'  # Исправлено на 'user.login'

# Инициализация базы данных
db.init_app(app)
login_manager.init_app(app)


from database.models.discount import Discount
from database.models.discountForm import DiscountForm
from database.models.priceForm import PriceForm
from database.models.servicePrice import ServicePrice

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

@app.route('/admin/price', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_price():
    form = PriceForm()
    prices = ServicePrice.query.order_by(ServicePrice.service_name).all()  # Используйте имя класса

    if form.validate_on_submit():
        # Проверяем, существует ли уже такая услуга
        existing_service = ServicePrice.query.filter_by(service_name=form.service_name.data).first()

        if existing_service:
            flash('Услуга с таким названием уже существует!', 'danger')
        else:
            new_price = ServicePrice(  # Используйте имя класса
                service_name=form.service_name.data,
                description=form.description.data,
                price=form.price.data
            )
            db.session.add(new_price)
            db.session.commit()
            flash('Услуга успешно добавлена!', 'success')
            return redirect(url_for('admin_price'))

    return render_template('admin_price.html', form=form, prices=prices)

@app.route('/admin/discounts', methods=['GET', 'POST'])
@login_required
def admin_discounts():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index.index'))

    form = DiscountForm()
    discounts = Discount.query.order_by(Discount.created_at.desc()).all()


    now = datetime.now()


    if request.method == 'POST':
        if form.validate_on_submit():
            discount = Discount(
                title=form.title.data,
                description=form.description.data,
                is_active=form.is_active.data,
                expires_at=form.expires_at.data
            )

            # Обработка загрузки изображения
            if form.image.data:
                try:
                    # Создаем папку если ее нет
                    upload_folder = 'static/uploads/discounts'
                    os.makedirs(upload_folder, exist_ok=True)

                    filename = secure_filename(form.image.data.filename)
                    unique_filename = f"{datetime.now().timestamp()}_{filename}"
                    filepath = os.path.join(upload_folder, unique_filename)

                    # Сохраняем файл
                    form.image.data.save(filepath)
                    discount.image = f"uploads/discounts/{unique_filename}"

                except Exception as e:
                    flash(f'Ошибка при загрузке изображения: {str(e)}', 'error')
                    return redirect(url_for('admin_discounts'))

            try:
                db.session.add(discount)
                db.session.commit()
                flash('Скидка успешно добавлена!', 'success')
                return redirect(url_for('admin_discounts'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при сохранении: {str(e)}', 'error')
                return redirect(url_for('admin_discounts'))

    return render_template('admin_discounts.html',
                           form=form,
                           discounts=discounts,
                           user=current_user,
                           now=now)




@app.route('/admin/discount/delete/<int:id>', methods=['POST'])
@login_required
def delete_discount(id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index.index'))

    discount = Discount.query.get_or_404(id)

    try:
        # Удаляем изображение если есть
        if discount.image:
            try:
                image_path = os.path.join('static', discount.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                flash(f'Ошибка при удалении изображения: {str(e)}', 'warning')

        # Удаляем из базы
        db.session.delete(discount)
        db.session.commit()
        flash('Скидка успешно удалена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')

    return redirect(url_for('admin_discounts'))



@app.route('/admin/cleanup_expired', methods=['POST'])
@login_required
def admin_cleanup_expired():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Доступ запрещен'})

    try:
        deleted_count = cleanup_expired_discounts()
        return jsonify({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



@app.route('/admin/discount/edit/<int:id>')
@login_required
def edit_discount_form(id):
    if not current_user.is_admin:
        return "Доступ запрещен", 403

    discount = Discount.query.get_or_404(id)

    # Создаем форму с данными скидки
    class EditDiscountForm(FlaskForm):
        title = StringField('Название', validators=[DataRequired()], default=discount.title)
        description = TextAreaField('Описание', validators=[DataRequired()], default=discount.description)
        is_active = BooleanField('Активна', default=discount.is_active)
        expires_at = DateField('Действует до', format='%Y-%m-%d', default=discount.expires_at)

    form = EditDiscountForm()

    return render_template('partials/edit_discount_form.html',
                           form=form,
                           discount=discount)




@app.route('/admin/discount/update/<int:id>', methods=['POST'])
@login_required
def update_discount(id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('admin_discounts'))

    discount = Discount.query.get_or_404(id)

    try:
        discount.title = request.form.get('title')
        discount.description = request.form.get('description')
        discount.is_active = 'is_active' in request.form
        expires_at = request.form.get('expires_at')
        discount.expires_at = datetime.strptime(expires_at, '%Y-%m-%d') if expires_at else None

        db.session.commit()
        flash('Скидка успешно обновлена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении: {str(e)}', 'error')

    return redirect(url_for('admin_discounts'))



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


@app.route('/admin/price/delete/<int:id>')
@login_required
@admin_required
def delete_price(id):
    price = ServicePrice.query.get_or_404(id)  # Используйте имя модели ServicePrice
    db.session.delete(price)
    db.session.commit()
    flash('Услуга успешно удалена!', 'success')
    return redirect(url_for('admin_price'))

@app.route('/admin/price/toggle/<int:id>')
@login_required
@admin_required
def toggle_price(id):
    price = ServicePrice.query.get_or_404(id)
    price.is_active = not price.is_active
    db.session.commit()
    flash('Статус услуги изменен!', 'success')
    return redirect(url_for('admin_price'))

@app.route('/admin/price/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_price(id):
    price = ServicePrice.query.get_or_404(id)
    form = PriceForm(obj=price)

    if form.validate_on_submit():
        form.populate_obj(price)
        db.session.commit()
        flash('Цена успешно обновлена!', 'success')
        return redirect(url_for('admin_price'))

    return render_template('edit_price.html', form=form, price=price)





























def cleanup_expired_discounts():
    """Удаляет просроченные скидки"""
    try:
        expired_count = Discount.query.filter(
            Discount.expires_at.isnot(None),
            Discount.expires_at < datetime.now()
        ).delete(synchronize_session=False)

        db.session.commit()
        print(f"Удалено {expired_count} просроченных скидок")
        return expired_count
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении просроченных скидок: {e}")
        return 0

# Запускаем очистку при старте приложения
with app.app_context():
    cleanup_expired_discounts()

























if __name__ == "__main__":
    # Запуск планировщика
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=cleanup_expired_discounts,
        trigger=IntervalTrigger(hours=1),
        id='cleanup_discounts',
        name='Cleanup expired discounts',
        replace_existing=True
    )
    scheduler.start()

    import atexit
    atexit.register(lambda: scheduler.shutdown())

    app.run(debug=True)
