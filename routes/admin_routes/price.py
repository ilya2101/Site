from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from admin_price import PriceForm
from database.engine import db
from database.models.servicePrice import ServicePrice
from database.models.priceForm import PriceForm







price_bp = Blueprint('admin_price', __name__, url_prefix='/admin/price')






@price_bp.route('/admin/price', methods=['GET', 'POST'])
@login_required
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
            return redirect(url_for('admin_price.admin_price'))

    return render_template('admin_price.html', form=form, prices=prices)



@price_bp.route('/admin/price/delete/<int:id>')
@login_required
def delete_price(id):
    price = ServicePrice.query.get_or_404(id)  # Используйте имя модели ServicePrice
    db.session.delete(price)
    db.session.commit()
    flash('Услуга успешно удалена!', 'success')
    return redirect(url_for('admin_price.admin_price'))

@price_bp.route('/admin/price/toggle/<int:id>')
@login_required
def toggle_price(id):
    price = ServicePrice.query.get_or_404(id)
    price.is_active = not price.is_active
    db.session.commit()
    flash('Статус услуги изменен!', 'success')
    return redirect(url_for('admin_price.admin_price'))

@price_bp.route('/admin/price/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_price(id):
    price = ServicePrice.query.get_or_404(id)
    form = PriceForm(obj=price)

    if form.validate_on_submit():
        form.populate_obj(price)
        db.session.commit()
        flash('Цена успешно обновлена!', 'success')
        return redirect(url_for('admin_price.admin_price'))

    return render_template('edit_price.html', form=form, price=price)