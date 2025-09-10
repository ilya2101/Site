from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ilya'

# Конфигурация БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_BINDS'] = {
    'applications': 'sqlite:///applications.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройка загрузки файлов
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'xls', 'xlsx', 'csv'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Создаем папку для загрузок, если ее нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Функция для проверки разрешенных расширений
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
# Модели должны быть определены перед импортом роутов
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def get_id(self):
        return str(self.id)

class Application(db.Model):
    __bind_key__ = 'applications'  # Указываем привязку к конкретной БД
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    car_brand = db.Column(db.String(50), nullable=False)
    car_model = db.Column(db.String(50), nullable=False)
    desired_date = db.Column(db.Date, nullable=False)
    desired_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')
    comment = db.Column(db.Text, default='')  # Добавляем поле для комментариев
    def __repr__(self):
        return f'<Application {self.id} - {self.name}>'

# Создаем модель для очереди
class Queue(db.Model):
    __bind_key__ = 'applications'  # Используем ту же базу
    __tablename__ = 'queue'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    car_brand = db.Column(db.String(50), nullable=False)
    car_model = db.Column(db.String(50), nullable=False)
    desired_date = db.Column(db.Date, nullable=False)
    desired_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='in_queue')
    comment = db.Column(db.Text, default='')
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с оригинальной заявкой
    application = db.relationship('Application', backref='queue_entries')

    # Модель для автомобилей в ремонте
class InService(db.Model):
    __bind_key__ = 'applications'
    __tablename__ = 'in_service'

    id = db.Column(db.Integer, primary_key=True)
    queue_id = db.Column(db.Integer, db.ForeignKey('queue.id'))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    car_brand = db.Column(db.String(50), nullable=False)
    car_model = db.Column(db.String(50), nullable=False)
    desired_date = db.Column(db.Date, nullable=False)
    desired_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_completion = db.Column(db.Date, nullable=True)
    estimated_cost = db.Column(db.String(100), nullable=True)
    comment = db.Column(db.Text, default='')
    work_list = db.Column(db.Text, default='')
    excel_file = db.Column(db.String(255), nullable=True)  # Путь к Excel файлу
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)

    queue_entry = db.relationship('Queue', backref='service_entries')


# Создаем таблицы в обеих базах данных
# Создаем таблицы в обеих базах данных
with app.app_context():




    # Создаем все таблицы заново
    db.create_all()
    db.create_all(bind_key='applications')

    print("Все таблицы созданы успешно!")


# Принудительное создание таблиц
with app.app_context():
    # Создаем таблицы по одной
    try:
        # Основная база
        User.__table__.create(db.engine, checkfirst=True)

        # База applications
        Application.__table__.create(db.get_engine(bind='applications'), checkfirst=True)
        Queue.__table__.create(db.get_engine(bind='applications'), checkfirst=True)
        InService.__table__.create(db.get_engine(bind='applications'), checkfirst=True)

        print("Все таблицы созданы принудительно!")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создаем таблицы (выполнить один раз)
with app.app_context():
    db.create_all()

def create_admin():
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

# Импортируем роуты после определения моделей и app


@app.route('/')
def index():
    return render_template("index.html")



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

        user = User.query.filter_by(phone=phone).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.is_admin:
                flash('Вы успешно вошли как администратор!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Вы успешно вошли!', 'success')
                return redirect(url_for('index'))
        else:
            flash('Неверный номер или пароль!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)

    # Получаем статистику
    new_requests_count = Application.query.filter_by(status='new').count()
    queue_count = Queue.query.count()
    total_requests = Application.query.count()

    # Получаем последние 5 заявок
    recent_requests = Application.query.order_by(Application.created_at.desc()).limit(5).all()

    return render_template('admin_dashboard.html',
                           user=current_user,
                           now=datetime.now(),
                           new_requests_count=new_requests_count,
                           queue_count=queue_count,
                           total_requests=total_requests,
                           recent_requests=recent_requests)

@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)



class ServiceRequest:
    pass


@app.route('/admin/requests')
@login_required
def view_requests():
    if not current_user.is_admin:
        abort(403)

    # Получаем все заявки из базы данных
    requests = Application.query.order_by(Application.created_at.desc()).all()
    return render_template('admin_requests.html',
                           requests=requests,
                           user=current_user)  # ДОБАВЬТЕ user=current_user


    # Получаем все заявки из базы данных
    requests = Application.query.order_by(Application.created_at.desc()).all()
    return render_template('admin_requests.html', requests=requests)

@app.route('/admin/request/update/<int:request_id>', methods=['POST'])
@login_required
def update_request(request_id):
    if not current_user.is_admin:
        abort(403)

    try:
        application = Application.query.get_or_404(request_id)

        # Обновляем данные
        application.name = request.form.get('name')
        application.phone = request.form.get('phone')
        application.car_brand = request.form.get('car_brand')
        application.car_model = request.form.get('car_model')
        application.desired_date = datetime.strptime(request.form.get('desired_date'), '%Y-%m-%d').date()
        application.desired_time = datetime.strptime(request.form.get('desired_time'), '%H:%M').time()
        application.comment = request.form.get('comment', '')

        db.session.commit()
        flash('Заявка успешно обновлена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении заявки: {str(e)}', 'danger')

    return redirect(url_for('view_requests'))


@app.route('/admin/request/comment/<int:request_id>', methods=['POST'])
@login_required
def add_comment(request_id):
    if not current_user.is_admin:
        abort(403)

    try:
        application = Application.query.get_or_404(request_id)
        comment = request.form.get('comment', '').strip()

        if comment:
            if application.comment:
                application.comment += f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M')}]: {comment}"
            else:
                application.comment = f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}]: {comment}"

            db.session.commit()
            flash('Комментарий добавлен!', 'success')
        else:
            flash('Комментарий не может быть пустым', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении комментария: {str(e)}', 'danger')

    return redirect(url_for('view_requests'))

@app.route('/admin/request/confirm/<int:request_id>')
@login_required
def confirm_request(request_id):
    if not current_user.is_admin:
        abort(403)

    try:
        application = Application.query.get_or_404(request_id)

        # Создаем запись в очереди
        queue_entry = Queue(
            application_id=application.id,
            name=application.name,
            phone=application.phone,
            car_brand=application.car_brand,
            car_model=application.car_model,
            desired_date=application.desired_date,
            desired_time=application.desired_time,
            created_at=application.created_at,
            comment=application.comment,
            status='in_queue'
        )

        # Добавляем в очередь и удаляем из заявок
        db.session.add(queue_entry)
        db.session.delete(application)
        db.session.commit()

        flash('Заявка перемещена в очередь!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при перемещении заявки: {str(e)}', 'danger')

    return redirect(url_for('view_requests'))

@app.route('/admin/request/delete/<int:request_id>')
@login_required
def delete_request(request_id):
    if not current_user.is_admin:
        abort(403)

    try:
        application = Application.query.get_or_404(request_id)
        db.session.delete(application)
        db.session.commit()
        flash('Заявка удалена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении заявки: {str(e)}', 'danger')

    return redirect(url_for('view_requests'))


@app.route('/submit_application', methods=['POST'])
def submit_application():
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            name = request.form['name']
            phone = request.form['phone']
            car_brand = request.form['carBrand']
            car_model = request.form['carModel']
            desired_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            desired_time = datetime.strptime(request.form['time'], '%H:%M').time()

            # Создаем новую заявку (сохраняем во вторую БД)
            new_application = Application(
                name=name,
                phone=phone,
                car_brand=car_brand,
                car_model=car_model,
                desired_date=desired_date,
                desired_time=desired_time
            )

            # Сохраняем в базу данных applications
            db.session.add(new_application)
            db.session.commit()

            # Возвращаем успешный ответ
            return jsonify({'success': True, 'message': 'Заявка успешно отправлена!'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Ошибка при отправке заявки: {str(e)}'})

@app.route('/admin/queue')
@login_required
def view_queue():
    if not current_user.is_admin:
        abort(403)

    # Получаем все записи из очереди
    queue_entries = Queue.query.order_by(Queue.moved_at.desc()).all()
    return render_template('admin_queue.html',
                           queue_entries=queue_entries,
                           user=current_user)

@app.route('/admin/queue/update/<int:queue_id>', methods=['POST'])
@login_required
def update_queue(queue_id):
    if not current_user.is_admin:
        abort(403)

    try:
        queue_entry = Queue.query.get_or_404(queue_id)

        # Обновляем данные
        queue_entry.name = request.form.get('name')
        queue_entry.phone = request.form.get('phone')
        queue_entry.car_brand = request.form.get('car_brand')
        queue_entry.car_model = request.form.get('car_model')
        queue_entry.desired_date = datetime.strptime(request.form.get('desired_date'), '%Y-%m-%d').date()
        queue_entry.desired_time = datetime.strptime(request.form.get('desired_time'), '%H:%M').time()
        queue_entry.comment = request.form.get('comment', '')

        db.session.commit()
        flash('Запись в очереди успешно обновлена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении записи: {str(e)}', 'danger')

    return redirect(url_for('view_queue'))

@app.route('/admin/queue/comment/<int:queue_id>', methods=['POST'])
@login_required
def add_queue_comment(queue_id):
    if not current_user.is_admin:
        abort(403)

    try:
        queue_entry = Queue.query.get_or_404(queue_id)
        comment = request.form.get('comment', '').strip()

        if comment:
            if queue_entry.comment:
                queue_entry.comment += f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M')}]: {comment}"
            else:
                queue_entry.comment = f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}]: {comment}"

            db.session.commit()
            flash('Комментарий добавлен!', 'success')
        else:
            flash('Комментарий не может быть пустым', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении комментария: {str(e)}', 'danger')

    return redirect(url_for('view_queue'))

@app.route('/admin/queue/to_service/<int:queue_id>', methods=['POST'])
@login_required
def move_to_service(queue_id):
    if not current_user.is_admin:
        abort(403)

    try:
        queue_entry = Queue.query.get_or_404(queue_id)

        # Обработка загрузки файла
        excel_filename = None
        if 'excel_file' in request.files:
            file = request.files['excel_file']
            if file and file.filename and allowed_file(file.filename):
                # Создаем безопасное имя файла
                filename = secure_filename(file.filename)
                # Добавляем timestamp для уникальности
                import time
                timestamp = str(int(time.time()))
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"

                # Сохраняем файл
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                excel_filename = filename


        # Создаем запись в ремонте
        service_entry = InService(
            queue_id=queue_entry.id,
            name=queue_entry.name,
            phone=queue_entry.phone,
            car_brand=queue_entry.car_brand,
            car_model=queue_entry.car_model,
            desired_date=queue_entry.desired_date,
            desired_time=queue_entry.desired_time,
            created_at=queue_entry.created_at,
            comment=queue_entry.comment,
            estimated_completion=datetime.strptime(request.form.get('estimated_completion'), '%Y-%m-%d').date() if request.form.get('estimated_completion') else None,
            estimated_cost=request.form.get('estimated_cost', ''),
            work_list=request.form.get('work_list', ''),
            excel_file=excel_filename
        )

        # Добавляем в ремонт и удаляем из очереди
        db.session.add(service_entry)
        db.session.delete(queue_entry)
        db.session.commit()

        flash('Автомобиль перемещен в ремонт!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при перемещении в ремонт: {str(e)}', 'danger')

    return redirect(url_for('view_queue'))

@app.route('/admin/queue/delete/<int:queue_id>')
@login_required
def delete_queue(queue_id):
    if not current_user.is_admin:
        abort(403)

    try:
        queue_entry = Queue.query.get_or_404(queue_id)
        db.session.delete(queue_entry)
        db.session.commit()
        flash('Запись из очереди удалена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении записи: {str(e)}', 'danger')

    return redirect(url_for('view_queue'))

@app.route('/admin/service')
@login_required
def view_service():
    if not current_user.is_admin:
        abort(403)

    # Получаем все записи в ремонте
    service_entries = InService.query.order_by(InService.moved_at.desc()).all()
    return render_template('admin_service.html',
                           service_entries=service_entries,
                           user=current_user)

@app.route('/admin/service/update/<int:service_id>', methods=['POST'])
@login_required
def update_service(service_id):
    if not current_user.is_admin:
        abort(403)

    try:
        service_entry = InService.query.get_or_404(service_id)

        # Обработка загрузки нового файла
        if 'excel_file' in request.files:
            file = request.files['excel_file']
            if file and file.filename and allowed_file(file.filename):
                # Удаляем старый файл, если он есть
                if service_entry.excel_file:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], service_entry.excel_file))
                    except:
                        pass

                # Создаем безопасное имя файла
                filename = secure_filename(file.filename)
                import time
                timestamp = str(int(time.time()))
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"

                # Сохраняем новый файл
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                service_entry.excel_file = filename

        # Обновляем данные
        service_entry.name = request.form.get('name')
        service_entry.phone = request.form.get('phone')
        service_entry.car_brand = request.form.get('car_brand')
        service_entry.car_model = request.form.get('car_model')
        service_entry.estimated_completion = datetime.strptime(request.form.get('estimated_completion'), '%Y-%m-%d').date() if request.form.get('estimated_completion') else None
        service_entry.estimated_cost = request.form.get('estimated_cost', '')
        service_entry.comment = request.form.get('comment', '')
        service_entry.work_list = request.form.get('work_list', '')

        db.session.commit()
        flash('Запись в ремонте успешно обновлена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении записи: {str(e)}', 'danger')

    return redirect(url_for('view_service'))

@app.route('/download/excel/<filename>')
@login_required
def download_excel(filename):
    if not current_user.is_admin:
        abort(403)

    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True
        )
    except:
        abort(404)

@app.route('/view/excel/<filename>')
@login_required
def view_excel(filename):
    if not current_user.is_admin:
        abort(403)

    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=False
        )
    except:
        abort(404)



@app.route('/admin/service/delete/<int:service_id>')
@login_required
def delete_service(service_id):
    if not current_user.is_admin:
        abort(403)

    try:
        service_entry = InService.query.get_or_404(service_id)

        # Удаляем файл, если он есть
        if service_entry.excel_file:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], service_entry.excel_file))
            except:
                pass

        db.session.delete(service_entry)
        db.session.commit()
        flash('Запись из ремонта удалена!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении записи: {str(e)}', 'danger')

    return redirect(url_for('view_service'))

@app.route('/about')
def about():
    render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contact.html')

@app.route('/discounts')
def discounts():
    return render_template('discounts.html')

@app.route('/price')
def prices():
    return render_template('price.html')

































if __name__ == '__main__':
    with app.app_context():
        create_admin()
    app.run(debug=True)