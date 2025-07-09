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
def hello():
    return render_template('index.html')

@app.route('/orders')
def orders():
    return render_template('orders.html')

from flask import request, redirect, url_for, flash

@app.route('/inventory')
def inventory():
    items = InventoryItem.query.all()
    return render_template('inventory.html', items=items)

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

@app.route('/reports')
def reports():
    return render_template('reports.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
