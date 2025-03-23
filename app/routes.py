# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Product, SupportProgram, SensorDevice, SensorReading, Permit, ComplianceReport, FarmerTask
from ai.crop_predictor import YieldPredictor
from datetime import datetime
from flask_wtf.csrf import generate_csrf
from app.forms import LoginForm, RegistrationForm, AddProductForm   


# Register Blueprint
routes_bp = Blueprint("routes", __name__)

@routes_bp.route('/')
def index():
    return render_template('index.html')

@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('routes.register'))

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            user_type=form.user_type.data,
            farm_size=form.farm_size.data if form.user_type.data == 'farmer' else 0,
            location=form.location.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('routes.dashboard'))
    
    # Handle GET requests or invalid form submissions
    return render_template('register.html', form=form)

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter(db.func.lower(User.email) == db.func.lower(form.email.data)).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('routes.dashboard'))
        
        flash('Invalid email or password', 'danger')
        return redirect(url_for('routes.login'))
    
    # Log form errors for debugging
    if form.errors:
        app.logger.error(f"Login form errors: {form.errors}")
    
    return render_template('login.html', form=form)

@routes_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

@routes_bp.route('/permits')
@login_required
def list_permits():
    if current_user.user_type != 'agent':
        abort(403)
    permits = Permit.query.all()
    return render_template('permits/permits_list.html', 
                         permits=permits,
                         current_user=current_user)

@routes_bp.route('/permits/new', methods=['GET', 'POST'])
@login_required
def new_permit():
    if current_user.user_type != 'agent':
        abort(403)
    
    if request.method == 'POST':
        # Date handling with proper datetime conversion
        issued_date = datetime.strptime(request.form['issued_date'], '%Y-%m-%d') if request.form['issued_date'] else None
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d') if request.form['expiry_date'] else None
        
        permit = Permit(
            permit_type=request.form['permit_type'],
            status=request.form.get('status', 'pending'),
            application_date=datetime.utcnow(),  # Now using properly imported datetime
            issued_date=issued_date,
            expiry_date=expiry_date,
            impact_assessment=request.form['impact_assessment'],
            user_id=request.form['applicant']
        )
        db.session.add(permit)
        db.session.commit()
        return redirect(url_for('routes.list_permits'))

    # For GET requests
    farmers = User.query.filter_by(user_type='farmer').all()
    return render_template('permits/new_permit.html',
                         farmers=farmers,
                         today=datetime.utcnow().date(),
                         csrf_token=generate_csrf())

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type == 'farmer':
        products = Product.query.filter_by(farmer_id=current_user.id).all()

        # Fetch sales data (Replace with real DB data)
        sales_labels = [p.name for p in products] if products else []  
        sales_data = [p.quantity for p in products] if products else []  

        return render_template('dashboard/farmer_dashboard.html', 
                               products=products, 
                               sales_labels=sales_labels, 
                               sales_data=sales_data)

    elif current_user.user_type == 'agent':
        farmers = User.query.filter_by(user_type='farmer').all()
        return render_template('dashboard/agent_dashboard.html', farmers=farmers)

    elif current_user.user_type == 'buyer':
        products = Product.query.all()
        return render_template('dashboard/buyer_dashboard.html', products=products)

    else:
        flash("Unauthorized user type!", "danger")
        return redirect(url_for('routes.index'))  # Redirect unauthorized users


@routes_bp.route('/marketplace')
def marketplace():
    products = Product.query.all()
    categories = db.session.query(Product.category.distinct()).all()
    return render_template('marketplace.html', 
                         products=products,
                         categories=[c[0] for c in categories])

@routes_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
    db.session.add(wishlist_item)
    db.session.commit()
    return jsonify({'success': True})

@routes_bp.route('/rate-product', methods=['POST'])
@login_required
def rate_product():
    data = request.get_json()
    rating = ProductRating(
        user_id=current_user.id,
        product_id=data['product_id'],
        rating=data['rating'],
        comment=data.get('comment')
    )
    db.session.add(rating)
    db.session.commit()
    return jsonify({'success': True})

# Farmer Dashboard Routes
@routes_bp.route('/farmer/tasks')
@login_required
def farmer_tasks():
    tasks = FarmerTask.query.filter_by(farmer_id=current_user.id).all()
    return render_template('dashboard/farmer/tasks.html', tasks=tasks)

@routes_bp.route('/farmer/crop-health')
@login_required
def crop_health():
    sensor_data = SensorReading.query.filter_by(farm_id=current_user.id).all()
    return render_template('dashboard/farmer/crop_health.html', 
                         sensor_data=sensor_data)

# Example AI prediction endpoint
@routes_bp.route('/predict-yield', methods=['POST'])
def predict_yield():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Missing request data'}), 400

    required_keys = ['soil_ph', 'rainfall', 'crop_type']
    for key in required_keys:
        if key not in data:
            return jsonify({'error': f'Missing key: {key}'}), 400

    try:
        # Ensure ai_model is defined
        prediction = ai_model.predict([
            data['soil_ph'], 
            data['rainfall'], 
            data['crop_type']
        ])
        return jsonify({'predicted_yield': f"{prediction[0]:.2f} tons/ha"})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes_bp.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProductForm()  # Create an instance of the form

    if form.validate_on_submit():
        name = form.name.data
        category = form.category.data
        price = form.price.data
        quantity = form.quantity.data
        description = form.description.data
        
        new_product = Product(
            name=name,
            category=category,
            price=price,
            quantity=quantity,
            description=description,
            farmer_id=current_user.id
        )

        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!", "success")
        return redirect(url_for('routes.dashboard'))

    return render_template('dashboard/farmer/add_product.html', form=form) 

@routes_bp.route('/delete_product/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.farmer_id != current_user.id:
        flash('You cannot delete this product', 'danger')
        return redirect(url_for('routes.dashboard'))

    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('routes.dashboard'))

# Additional Routes
@routes_bp.route('/payment/success')
def payment_success():
    return render_template('payment_success.html')

@routes_bp.route('/programs')
def support_programs():
    programs = SupportProgram.query.all()
    return render_template('programs.html', programs=programs)

@routes_bp.route('/sensor-data')
@login_required
def sensor_data():
    if current_user.user_type not in ['agent', 'farmer']:
        abort(403)
    sensor_readings = SensorReading.query.filter_by(farm_id=current_user.id).all()
    return render_template('sensor_data.html', readings=sensor_readings)


@routes_bp.route('/predict-yield-ml', methods=['POST']) 
@login_required
def predict_yield_ml():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Missing request data'}), 400

    required_keys = ['soil_ph', 'rainfall', 'temp', 'crop_type', 'elevation']
    for key in required_keys:
        if key not in data:
            return jsonify({'error': f'Missing key: {key}'}), 400

    try:
        predictor = YieldPredictor()
        prediction = predictor.predict(
            data['soil_ph'],
            data['rainfall'],
            data['temp'],
            data['crop_type'],
            data['elevation'],
            current_user.farm_size
        )
        return jsonify({'predicted_yield': f"{prediction:.2f} tons/ha"})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes_bp.route('/agent/farmer-management')
@login_required
def manage_farmers():
    if current_user.user_type != 'agent':
        abort(403)
    farmers = User.query.filter_by(user_type='farmer').all()
    return render_template('dashboard/agent/manage_farmers.html', farmers=farmers)

# FARMER ROUTES
@routes_bp.route('/farmer/planting-calendar')
@login_required
def planting_calendar():
    if current_user.user_type != 'farmer':
        abort(403)
    schedule = PlantingSchedule.query.filter_by(farmer_id=current_user.id).all()
    return render_template('dashboard/farmer/planting_calendar.html', schedule=schedule)

@routes_bp.route('/farmer/subsidies')
@login_required
def subsidy_applications():
    if current_user.user_type != 'farmer':
        abort(403)
    applications = SubsidyApplication.query.filter_by(farmer_id=current_user.id).all()
    return render_template('dashboard/farmer/subsidy_applications.html', applications=applications)

# BUYER ROUTES
@routes_bp.route('/buyer/cart')
@login_required
def view_cart():
    if current_user.user_type != 'buyer':
        abort(403)
    cart_items = CartItem.query.filter_by(buyer_id=current_user.id).all()
    return render_template('dashboard/buyer/cart.html', cart_items=cart_items)

@routes_bp.route('/buyer/favorites')
@login_required
def favorites():
    if current_user.user_type != 'buyer':
        abort(403)
    favorites = FavoriteProduct.query.filter_by(buyer_id=current_user.id).all()
    return render_template('dashboard/buyer/favorites.html', favorites=favorites)

@routes_bp.route('/compliance-reports')
@login_required
def compliance_reports():
    # Choose sidebar dynamically based on user role
    if current_user.user_type == 'farmer':
        sidebar_template = 'dashboard/farmer/sidebar.html'
    elif current_user.user_type == 'agent':
        sidebar_template = 'dashboard/agent/sidebar.html'
    else:  # Default to buyer sidebar
        sidebar_template = 'dashboard/buyer/sidebar.html'

    return render_template('compliance_reports.html', sidebar_template=sidebar_template)

@routes_bp.route('/create-task', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        deadline = request.form.get('deadline')

        if not title or not deadline:
            flash('Title and deadline are required', 'danger')
            return redirect(url_for('routes.farmer_tasks'))

        new_task = FarmerTask(
            title=title,
            description=description,
            deadline=deadline,
            farmer_id=current_user.id
        )

        db.session.add(new_task)
        db.session.commit()
        flash('New task created successfully!', 'success')

        return redirect(url_for('routes.farmer_tasks'))

    return render_template('dashboard/farmer/tasks.html')  # Ensure this exists
