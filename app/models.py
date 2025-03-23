# app/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(20))  # farmer, buyer, agent
    farm_size = db.Column(db.Float)
    location = db.Column(db.String(100))
    products = db.relationship('Product', backref='farmer', lazy=True)
    permits = db.relationship('Permit', backref='applicant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # crops, livestock
    price = db.Column(db.Float)
    quantity = db.Column(db.Float)
    description = db.Column(db.Text)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SupportProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    deadline = db.Column(db.Date)
    application_link = db.Column(db.String(200))

class Permit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    permit_type = db.Column(db.String(50), nullable=False)  # environmental, agricultural, etc.
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    issued_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    impact_assessment = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class LandRegistry:
    def register_transfer(self, seller, buyer, parcel_id):
        tx_hash = contract.functions.transferOwnership(
            seller, buyer, parcel_id
        ).transact()
        return tx_hash

class SensorDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sensor_type = db.Column(db.String(50))  # soil, weather

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('sensor_device.device_id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    soil_moisture = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Agent Models
class ComplianceReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    inspection_date = db.Column(db.DateTime)
    status = db.Column(db.String(20))  # compliant/non-compliant
    report_url = db.Column(db.String(200))
    findings = db.Column(db.Text)
    inspector_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    farm = db.relationship('User', foreign_keys=[farm_id])
    inspector = db.relationship('User', foreign_keys=[inspector_id])

# Farmer Models
class PlantingSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    crop_type = db.Column(db.String(50))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

# Buyer Models
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Float)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Float)
    total = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    
class ProductRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FarmerTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)