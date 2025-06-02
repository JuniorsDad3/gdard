from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length
import email_validator
from flask_migrate import Migrate
from web3 import Web3
import logging
from flask_talisman import Talisman
from dotenv import load_dotenv
from collections import defaultdict
from flask_wtf.csrf import CSRFProtect
import os
import boto3
import random
import string
import secrets
import openai
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = os.getenv("SECRET_KEY", "default-secret-key")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Talisman(app)
migrate = Migrate(app, db)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'  # Explicitly set the table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Poultry', 'Poultry'),
        ('Vegetables', 'Vegetables'),
        ('Fruits', 'Fruits'),
        ('Dairy', 'Dairy'),
        ('Grains', 'Grains')
    ], validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('List Product')

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', products=user_products)

@app.route('/marketplace')
def marketplace():
    products = Product.query.all()
    return render_template('marketplace.html', products=products)

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    form = ProductForm()
    if form.validate_on_submit():
        # Extract product data from the form
        product_name = form.name.data
        category = form.category.data
        price = form.price.data
        description = form.description.data
        # Save the product to your database or (for demo) add to the list
        new_product = Product(
            name=product_name,
            category=category,
            price=price,
            description=description,
            user_id=current_user.id
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product listed successfully!', 'success')
        return redirect(url_for('marketplace'))
    return render_template('sell.html', form=form)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    # Example AI response (replace with actual AI integration)
    ai_response = f"AI Response: We have received your query: {user_message}"
    return jsonify({'response': ai_response})

# IoT Integration (Placeholder)
@app.route('/iot/data', methods=['POST'])
def iot_data():
    data = request.json
    # Process IoT data (e.g., soil moisture, temperature)
    logger.info(f"Received IoT data: {data}")
    return jsonify({'status': 'success', 'message': 'IoT data received'})

# Blockchain Integration (Placeholder)
@app.route('/blockchain/record', methods=['POST'])
def blockchain_record():
    data = request.json
    # Add data to blockchain (e.g., product traceability)
    logger.info(f"Blockchain record: {data}")
    return jsonify({'status': 'success', 'message': 'Blockchain record created'})

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
