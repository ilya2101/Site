from datetime import datetime
from flask import render_template, Blueprint, request, jsonify
from flask_login import current_user

from database.engine import db
from database.models.application import Application
from database.models.discount import Discount
from database.models.servicePrice import ServicePrice

index_route = Blueprint('index', __name__, template_folder='../../templates')


@index_route.route('/')
def index():
    return render_template("index.html")


@index_route.route('/submit_application', methods=['POST'])
def submit_application():
    if request.method == 'POST':
        try:
            name = request.form['name']
            phone = request.form['phone']
            car_brand = request.form['carBrand']
            car_model = request.form['carModel']
            desired_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            desired_time = datetime.strptime(request.form['time'], '%H:%M').time()

            new_application = Application(
                name=name,
                phone=phone,
                car_brand=car_brand,
                car_model=car_model,
                desired_date=desired_date,
                desired_time=desired_time
            )

            db.session.add(new_application)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Заявка успешно отправлена!'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Ошибка при отправке заявки: {str(e)}'})


@index_route.route('/about', endpoint='about')
def about():
    return render_template('about.html')


@index_route.route('/contacts', endpoint='contacts')
def contacts():
    return render_template('contacts.html')


@index_route.route('/discounts', endpoint='discounts')
def discounts():
    active_discounts = Discount.query.filter(
        Discount.is_active == True,
        (Discount.expires_at.is_(None)) | (Discount.expires_at >= datetime.now())
    ).order_by(Discount.created_at.desc()).all()

    return render_template('discounts.html', discounts=active_discounts, user=current_user)


@index_route.route('/price', endpoint='price')
def price():
    active_prices = ServicePrice.query.filter_by(is_active=True).order_by(ServicePrice.service_name).all()
    return render_template('price.html', prices=active_prices)
