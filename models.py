from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy (to be used in app.py)
db = SQLAlchemy()

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'<InventoryItem {self.name}>'
