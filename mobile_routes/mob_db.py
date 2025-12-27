from flask import Blueprint, request, jsonify
from datetime import datetime
from database.engine import db
from database.models.application import Application  # Импортируем вашу модель

mob_db = Blueprint('mobile', __name__, url_prefix='/api')

@mob_db.route('/applications', methods=['POST'])
def create_application():
    try:
        data = request.get_json()
        print("📱 [MOBILE API] Получена заявка:", data)

        # Валидация обязательных полей
        required_fields = ['name', 'phone', 'carBrand', 'carModel', 'date', 'time']
        missing_fields = []

        for field in required_fields:
            if field not in data or not str(data.get(field, '')).strip():
                missing_fields.append(field)

        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Не заполнены обязательные поля: {", ".join(missing_fields)}'
            }), 400

        # Конвертируем время из строки "15:00" в объект времени
        try:
            time_obj = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Неверный формат времени. Используйте HH:MM'
            }), 400

        # Конвертируем дату из строки "2025-12-30" в объект даты
        try:
            date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Неверный формат даты. Используйте YYYY-MM-DD'
            }), 400

        # Создаем новую заявку в БД
        new_application = Application(
            name=data['name'].strip(),
            phone=data['phone'].strip(),
            car_brand=data['carBrand'].strip(),
            car_model=data['carModel'].strip(),
            desired_date=date_obj,
            desired_time=time_obj,
            status='Новая',
            created_at=datetime.utcnow(),
            comment='Заявка из мобильного приложения'
        )

        # Сохраняем в БД
        db.session.add(new_application)
        db.session.commit()

        print(f"✅ Заявка #{new_application.id} сохранена в БД")

        return jsonify({
            'success': True,
            'message': 'Заявка успешно отправлена! Скидка 10% активирована.',
            'discount': '10%',
            'contact_time': '15 минут',
            'application_id': new_application.id,
            'data': {
                'id': new_application.id,
                'name': new_application.name,
                'phone': new_application.phone,
                'car_brand': new_application.car_brand,
                'car_model': new_application.car_model,
                'date': new_application.desired_date.strftime('%Y-%m-%d'),
                'time': new_application.desired_time.strftime('%H:%M'),
                'status': new_application.status,
                'created_at': new_application.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при сохранении в БД: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Ошибка базы данных: {str(e)}'
        }), 500

@mob_db.route('/applications/health', methods=['GET'])
def health_check():
    try:
        # Проверяем подключение к БД
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'

    return jsonify({
        'status': 'healthy',
        'service': 'mobile_api',
        'database': db_status,
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'POST /api/applications': 'Создание заявки',
            'GET /api/applications/health': 'Проверка здоровья'
        }
    }), 200

@mob_db.route('/applications/test', methods=['GET'])
def test_route():
    """Тестовый маршрут для проверки"""
    return jsonify({
        'message': 'Mobile API работает!',
        'status': 'ok',
        'time': datetime.now().isoformat()
    }), 200