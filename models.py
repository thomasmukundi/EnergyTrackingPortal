# models.py
from __init__ import db  # Import db from __init__ using explicit import
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)  # False for regular users, True for admins
    electricity_meter_number = db.Column(db.String(100), nullable=True)  # Nullable if not all users will have this info
    water_meter_number = db.Column(db.String(100), nullable=True)  # Nullable if not all users will have this info

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class EnergyUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Assuming you have a user model with id as primary key
    meter_number = db.Column(db.String(100))
    units_used = db.Column(db.Float)  # This can be kWh for electricity, liters for fuel, m³ for gas, etc.
    date_recorded = db.Column(db.DateTime, default=db.func.current_timestamp())
    energy_type = db.Column(db.String(50))

    def __repr__(self):
        return f'<EnergyUsage {self.energy_type} {self.units_used}>'


class Recommendations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    energy_type = db.Column(db.String(50))
    recommendation = db.Column(db.Text)

    def __repr__(self):
        return f'<Recommendation {self.date}: {self.recommendation}>'