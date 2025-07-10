from flask import Flask, render_template
from models import db, InventoryItem
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-12345'  # Change this to a strong, unique value for production

# Configure PostgreSQL database (default to SQLite if not set)
POSTGRES_URI = os.environ.get('DATABASE_URL')
if POSTGRES_URI:
    app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_URI
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Note: Requires psycopg2 for PostgreSQL

db.init_app(app)

@app.route('/')
def dashboard():
    from models import Order, InventoryItem
    recent_orders = Order.query.order_by(Order.date.desc()).limit(5).all()
    recent_items = InventoryItem.query.order_by(InventoryItem.id.desc()).limit(5).all()
    return render_template('dashboard.html', recent_orders=recent_orders, recent_items=recent_items)


@app.route('/orders')
def orders():
    from models import Order, OrderItem
    orders = Order.query.order_by(Order.date.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/orders/<int:order_id>')
def order_detail(order_id):
    from models import Order, OrderItem, InventoryItem
    order = Order.query.get_or_404(order_id)
    order_items = (
        OrderItem.query.filter_by(order_id=order.id)
        .join(InventoryItem, OrderItem.inventory_item_id == InventoryItem.id)
        .add_entity(InventoryItem)
        .all()
    )
    return render_template('order_detail.html', order=order, order_items=order_items)

@app.route('/orders/add', methods=['GET', 'POST'])
def add_order():
    from models import Order, OrderItem, InventoryItem
    if request.method == 'POST':
        import datetime
        date = request.form.get('date') or datetime.date.today().isoformat()
        items = []
        total = 0.0
        # Parse dynamic order items from form
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        for item_id, qty, price in zip(item_ids, quantities, prices):
            if not item_id or not qty or int(qty) <= 0:
                continue
            item = InventoryItem.query.get(int(item_id))
            if item:
                price_at_sale = float(price)
                total += int(qty) * price_at_sale
                items.append({'item': item, 'quantity': int(qty), 'price_at_sale': price_at_sale})
        if not items:
            flash('Please add at least one order item.', 'danger')
            return redirect(url_for('add_order'))
        order = Order(date=date, total=total)
        db.session.add(order)
        db.session.flush()  # get order.id
        for entry in items:
            order_item = OrderItem(
                order_id=order.id,
                inventory_item_id=entry['item'].id,
                quantity=entry['quantity'],
                price_at_sale=entry['price_at_sale']
            )
            db.session.add(order_item)
        db.session.commit()
        flash(f'Order #{order.id} added!', 'success')
        return redirect(url_for('orders'))
    import datetime
    inventory_items = InventoryItem.query.order_by(InventoryItem.name).all()
    today = datetime.date.today().isoformat()
    return render_template('add_order.html', inventory_items=inventory_items, today=today)

@app.route('/orders/edit/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    from models import Order, OrderItem, InventoryItem
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        import datetime
        date = request.form.get('date') or datetime.date.today().isoformat()
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        items = []
        total = 0.0
        for item_id, qty, price in zip(item_ids, quantities, prices):
            if not item_id or not qty or int(qty) <= 0:
                continue
            item = InventoryItem.query.get(int(item_id))
            if item:
                price_at_sale = float(price)
                total += int(qty) * price_at_sale
                items.append({'item': item, 'quantity': int(qty), 'price_at_sale': price_at_sale})
        if not items:
            flash('Please add at least one order item.', 'danger')
            return redirect(url_for('edit_order', order_id=order.id))
        order.date = date
        order.total = total
        # Remove existing order items
        OrderItem.query.filter_by(order_id=order.id).delete()
        for entry in items:
            order_item = OrderItem(
                order_id=order.id,
                inventory_item_id=entry['item'].id,
                quantity=entry['quantity'],
                price_at_sale=entry['price_at_sale']
            )
            db.session.add(order_item)
        db.session.commit()
        flash(f'Order #{order.id} updated!', 'success')
        return redirect(url_for('orders'))
    inventory_items = InventoryItem.query.order_by(InventoryItem.name).all()
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    today = order.date.isoformat() if hasattr(order.date, 'isoformat') else str(order.date)
    return render_template('edit_order.html', order=order, order_items=order_items, inventory_items=inventory_items, today=today)

from sqlalchemy.exc import IntegrityError
@app.route('/orders/delete/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    from models import Order, OrderItem
    order = Order.query.get_or_404(order_id)
    try:
        OrderItem.query.filter_by(order_id=order.id).delete()
        db.session.delete(order)
        db.session.commit()
        flash(f'Order #{order.id} deleted!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f'Cannot delete order #{order.id}: it is referenced elsewhere.', 'danger')
    return redirect(url_for('orders'))

from flask import request, redirect, url_for, flash

@app.route('/inventory')
def inventory():
    items = InventoryItem.query.all()
    low_stock_items = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.reorder_level).all()
    nearing_low_stock_items = InventoryItem.query.filter(
        (InventoryItem.quantity > InventoryItem.reorder_level) &
        (InventoryItem.quantity <= InventoryItem.reorder_level + (0.2 * InventoryItem.reorder_level))
    ).all()
    return render_template('inventory.html', items=items, low_stock_items=low_stock_items, nearing_low_stock_items=nearing_low_stock_items)

@app.route('/inventory/add', methods=['GET', 'POST'])
def add_inventory_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        quantity = int(request.form['quantity'])
        reorder_level = int(request.form['reorder_level'])
        price = float(request.form['price'])
        new_item = InventoryItem(
            name=name,
            description=description,
            quantity=quantity,
            reorder_level=reorder_level,
            price=price
        )
        db.session.add(new_item)
        db.session.commit()
        flash(f'Inventory item "{name}" added!', 'success')
        return redirect(url_for('inventory'))
    return render_template('add_inventory_item.html')

@app.route('/inventory/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.quantity = int(request.form['quantity'])
        item.reorder_level = int(request.form['reorder_level'])
        item.price = float(request.form['price'])
        db.session.commit()
        flash(f'Inventory item "{item.name}" updated!', 'success')
        return redirect(url_for('inventory'))
    return render_template('edit_inventory_item.html', item=item)

from sqlalchemy.exc import IntegrityError

@app.route('/inventory/delete/<int:item_id>', methods=['POST'])
def delete_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash(f'Inventory item "{item.name}" deleted!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash(f'Cannot delete "{item.name}": it is used in one or more orders.', 'danger')
    return redirect(url_for('inventory'))

@app.route('/reports')
def reports():
    # List available reports
    available_reports = [
        {"name": "Inventory Valuation", "endpoint": "inventory_valuation_report"},
        {"name": "Sales Summary", "endpoint": "sales_summary_report"},
        {"name": "Low Stock", "endpoint": "low_stock_report"},
    ]
    return render_template('reports.html', available_reports=available_reports)

@app.route('/reports/inventory_valuation')
def inventory_valuation_report():
    from models import InventoryItem
    items = InventoryItem.query.all()
    total_value = sum(item.quantity * item.price for item in items)
    return render_template('inventory_valuation_report.html', items=items, total_value=total_value)

from flask import request
import datetime

@app.route('/reports/sales_summary', methods=['GET', 'POST'])
def sales_summary_report():
    from models import Order, OrderItem, InventoryItem
    selected_date = request.form.get('date') if request.method == 'POST' else datetime.date.today().isoformat()
    orders = Order.query.filter(Order.date == selected_date).all()
    order_ids = [o.id for o in orders]
    order_items = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).all() if order_ids else []
    # Build item sales summary
    item_sales = {}
    for oi in order_items:
        item = InventoryItem.query.get(oi.inventory_item_id)
        if item:
            if item.name not in item_sales:
                item_sales[item.name] = {"quantity": 0, "total": 0.0}
            item_sales[item.name]["quantity"] += oi.quantity
            item_sales[item.name]["total"] += oi.quantity * oi.price_at_sale
    total_sales = sum(order.total for order in orders)
    return render_template('sales_summary_report.html', selected_date=selected_date, orders=orders, total_sales=total_sales, item_sales=item_sales)

@app.route('/reports/low_stock')
def low_stock_report():
    from models import InventoryItem
    low_stock_items = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.reorder_level).all()
    return render_template('low_stock_report.html', low_stock_items=low_stock_items)

import os

# Ensure tables are created on every startup (including Gunicorn)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(host='0.0.0.0', debug=debug)
