from flask import Blueprint, request, jsonify
from datetime import datetime
from database.engine import db
from database.models.application import Application

mobile_bp = Blueprint('mobile', __name__)

@mobile_bp.route('/api/applications', methods=['POST'])
def create_application():
    try:
        data = request.get_json()

        # Валидация полей
        required_fields = ['name', 'phone', 'carBrand', 'carModel', 'date', 'time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Поле {field} обязательно'}), 400

        # Создаем заявку
        new_application = Application(
            name=data.get('name'),
            phone=data.get('phone'),
            car_brand=data.get('carBrand'),
            car_model=data.get('carModel'),
            desired_date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            desired_time=datetime.strptime(data.get('time'), '%H:%M').time(),
            status='Новая',
            comment='Заявка с мобильного приложения'
        )

        db.session.add(new_application)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Заявка создана! Скидка 10% активирована.',
            'id': new_application.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500