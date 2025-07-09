from flask import Flask, render_template
from models import db
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables

app = Flask(__name__)

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

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
