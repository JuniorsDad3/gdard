# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask import current_app
from app.models import User, Product, SupportProgram, SensorDevice, SensorReading, Permit, ComplianceReport, FarmerTask, FundingApplication,ComplianceCase
from ai.crop_predictor import YieldPredictor
from datetime import datetime
from flask_wtf.csrf import generate_csrf
from app.forms import LoginForm, RegistrationForm, AddProductForm   
from app.email import send_email


# Register Blueprint
routes_bp = Blueprint("routes", __name__)

@routes_bp.route('/')
def index():
    return render_template('index.html')

@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST' and form.user_type.data != 'farmer':
        form.farm_size.data = 0
    if form.validate_on_submit():
        existing_user = User.find_by_email(form.email.data)
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('routes.register'))  # redirect back to registration form

        new_user_data = {
            "username": form.username.data,
            "email": form.email.data,
            "password": form.password.data,
            "user_type": form.user_type.data,
            "farm_size": form.farm_size.data if form.user_type.data == 'farmer' else 0,
            "location": form.location.data,
            "phone": "",         # optional fields if not in the form
            "avatar_url": "",    # optional fields
        }

        created_user = User.create(**new_user_data)

        send_email(
            subject="Welcome to GDARD!",
            recipients=[created_user.email],
            user=created_user
        )

        flash('Registration successful!', 'success')
        return redirect(url_for('routes.login'))

    if request.method == 'POST':
        current_app.logger.debug("Register form errors: %s", form.errors)

    return render_template('register.html', form=form)

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        # Use the class‐method you added on User:
        user = User.find_by_email(form.email.data)

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('routes.dashboard'))

        flash('Invalid email or password', 'danger')
        return redirect(url_for('routes.login'))

    # If POST with validation errors, log them
    if request.method == 'POST' and form.errors:
        current_app.logger.debug("Login form errors: %s", form.errors)

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
    # ExcelModel.all() returns list of dicts; wrap to Permit objects
    permits = [Permit(**row) for row in Permit.all()]
    return render_template('permits/permits_list.html', permits=permits)

@routes_bp.route('/permits/new', methods=['GET', 'POST'])
@login_required
def new_permit():
    if current_user.user_type != 'agent':
        abort(403)

    if request.method == 'POST':
        issued_date = request.form['issued_date'] or None
        expiry_date = request.form['expiry_date'] or None

        # Permit.create returns the new record as a dict or instance
        new = Permit.create(
            permit_type=request.form['permit_type'],
            user_id=request.form['applicant'],
            impact_assessment=request.form['impact_assessment'],
            issued_date=issued_date and datetime.strptime(issued_date, '%Y-%m-%d'),
            expiry_date=expiry_date and datetime.strptime(expiry_date, '%Y-%m-%d')
        )

        flash("Permit submitted!", "success")
        return redirect(url_for('routes.list_permits'))

    farmers = [User(**row) for row in User.find(user_type='farmer')]
    return render_template('permits/new_permit.html',
                           farmers=farmers,
                           today=datetime.utcnow().date(),
                           csrf_token=generate_csrf())

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    # Only farmers see this enriched dashboard
    if current_user.user_type == 'farmer':
        # 1) Products
        all_rows    = Product.all()
        farmer_id   = int(current_user.id)
        products    = [
            Product(**row)
            for row in all_rows
            if int(row.get('owner_id', -1)) == farmer_id
        ]
        sales_labels = [p.name     for p in products]
        sales_data   = [p.quantity for p in products]

        # 2) Pending funding applications (status == 'pending')
        #    using your ExcelModel API
        app_rows     = FundingApplication.all()
        pending_apps = sum(1 for r in app_rows if r.get('status') == 'pending')

        # 3) Outstanding compliance tasks (status == 'open')
        case_rows       = ComplianceCase.all()
        farmer_field     = 'user_id'  
        compliance_tasks = sum(
            1 for r in case_rows
            if int(r.get('farm_id', -1)) == farmer_id and r.get('status') == 'open'
        )

        # 4) Example sensor data (replace with real readings later)
        sensor_data = {
            'moisture':    45,
            'temperature': 22.5,
            'light':       800
        }

        return render_template(
            'dashboard/farmer_dashboard.html',
            product=products,
            products=products,
            sales_labels=sales_labels,
            sales_data=sales_data,
            pending_apps=pending_apps,
            compliance_tasks=compliance_tasks,
            sensor_data=sensor_data,
            applications=[FundingApplication(**r) for r in app_rows]
        )

    # Agents get a farmers list
    elif current_user.user_type == 'agent':
        farmers = [User(**row) for row in User.find(user_type='farmer')]
        return render_template('dashboard/agent_dashboard.html', farmers=farmers)

    # Buyers see all products
    elif current_user.user_type == 'buyer':
        products = [Product(**row) for row in Product.all()]
        return render_template('dashboard/buyer_dashboard.html', products=products, product=product)

    # Anything else is unauthorized
    flash("Unauthorized user type!", "danger")
    return redirect(url_for('routes.index'))


@routes_bp.route('/marketplace')
def marketplace():
    products = [Product(**row) for row in Product.all()]
    categories = sorted({p.category for p in products})
    return render_template('marketplace.html',
                           products=products,
                           categories=categories)

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
    data = request.get_json() or {}
    rating = ProductRating.create(
        user_id=current_user.id,
        product_id=data.get('product_id'),
        rating=data.get('rating'),
        comment=data.get('comment', '')
    )
    return jsonify({'success': True})

# Farmer Dashboard Routes
@routes_bp.route('/farmer/tasks')
@login_required
def farmer_tasks():
    rows = FarmerTask.find(farmer_id=current_user.id)
    tasks = [FarmerTask(**r) for r in rows]
    return render_template('dashboard/farmer/tasks.html', tasks=tasks)

@routes_bp.route('/farmer/crop-health')
@login_required
def crop_health():
    rows = SensorReading.find(user_id=current_user.id)
    sensor_data = [SensorReading(**r) for r in rows]
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

@routes_bp.route('/farm-compliance')
@login_required
def farm_compliance():
    return render_template('farmer/farm_compliance.html', compliance_items=compliance_items)

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

# ================== Authentication Routes ==================
@routes_bp.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    # Add password reset logic here
    return render_template('password_reset.html')

# ================== Marketplace Routes ==================
@routes_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    rows = Product.find(id=product_id)
    if not rows:
        abort(404)
    product = Product(**rows[0])
    return render_template('product_detail.html', product=product)

@routes_bp.route('/cart')
@login_required
def shopping_cart():
    if current_user.user_type != 'buyer':
        abort(403)
    rows = CartItem.find(buyer_id=current_user.id)
    cart_items = [CartItem(**r) for r in rows]
    return render_template('shopping_cart.html', cart_items=cart_items)

# ================== Funding & Applications ==================
@routes_bp.route('/funding/apply', methods=['GET', 'POST'])
@login_required
def funding_application():
    if current_user.user_type != 'farmer':
        abort(403)
    # Add funding application logic here
    return render_template('funding_application.html')

@routes_bp.route('/applications/<int:app_id>')
@login_required
def application_detail(app_id):
    rows = FundingApplication.find(id=app_id)
    if not rows:
        abort(404)
    app = FundingApplication(**rows[0])
    if app.farmer_id != current_user.id and current_user.user_type != 'agent':
        abort(403)
    return render_template('application_detail.html', application=app)

@routes_bp.route('/funding/applications')
@login_required
def funding_applications():
    if current_user.user_type != 'agent':
        abort(403)
    # all records, sorted by submitted_date desc
    apps = sorted(
        (FundingApplication(**r) for r in FundingApplication.all()),
        key=lambda x: x.submitted_date,
        reverse=True
    )
    return render_template('dashboard/funding_applications.html',
                           funding_apps=apps)

@routes_bp.route('/submit-application', methods=['GET', 'POST'])
@login_required
def submit_application():
    if request.method == 'POST':
        # TODO: Handle form submission, save to Excel or data store
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('routes.submit_application'))

    return render_template('farmer/submit_application.html')

@routes_bp.route('/manage-listings')
@login_required
def manage_listings():
    # You can load data from Excel or a placeholder list for now
    listings = []  # Replace with actual logic
    return render_template('farmer/manage_listings.html', listings=listings)

# ================== User Management Routes ==================
@routes_bp.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    # Add profile update logic here
    return render_template('profile_settings.html')

@routes_bp.route('/agent/users')
@login_required
def user_list():
    if current_user.user_type != 'agent':
        abort(403)
    users = [User(**r) for r in User.all()]
    return render_template('user_list.html', users=users)

@routes_bp.route('/agent/users/<int:user_id>')
@login_required
def user_detail(user_id):
    if current_user.user_type != 'agent':
        abort(403)
    rows = User.find(id=user_id)
    if not rows:
        abort(404)
    user = User(**rows[0])
    return render_template('user_detail.html', user=user)

# ================== Compliance Routes ==================
@routes_bp.route('/compliance/<int:case_id>')
@login_required
def compliance_detail(case_id):
    rows = ComplianceCase.find(id=case_id)
    if not rows:
        abort(404)
    case = ComplianceCase(**rows[0])
    if current_user.user_type == 'farmer' and case.farm_id != current_user.id:
        abort(403)
    return render_template('compliance_detail.html', case=case)

@routes_bp.route('/agent/inspections', methods=['GET', 'POST'])
@login_required
def inspection_scheduler():
    if current_user.user_type != 'agent':
        abort(403)
    # Add inspection scheduling logic here
    return render_template('inspection_scheduler.html')

# ================== Order Management ==================
@routes_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    rows = Order.find(id=order_id)
    if not rows:
        abort(404)
    order = Order(**rows[0])
    if current_user.user_type == 'buyer' and order.buyer_id != current_user.id:
        abort(403)
    return render_template('order_detail.html', order=order)

@routes_bp.route('/my-orders')
@login_required
def my_orders():
    if current_user.user_type == 'buyer':
        rows = Order.find(buyer_id=current_user.id)
    elif current_user.user_type == 'farmer':
        rows = Order.find(farmer_id=current_user.id)
    else:
        rows = []

    orders = [Order(**row) for row in rows]
    return render_template('my_orders.html', orders=orders)

@routes_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if current_user.user_type != 'buyer':
        abort(403)
    # Add checkout logic here
    return render_template('checkout.html')

@routes_bp.route('/invoices/<int:order_id>')
@login_required
def invoice_template(order_id):
    rows = Order.find(id=order_id)
    if not rows:
        abort(404)
    order = Order(**rows[0])
    return render_template('invoice_template.html', order=order)

# ================== Analytics Routes ==================
@routes_bp.route('/analytics/sales')
@login_required
def sales_analytics():
    if current_user.user_type not in ['agent', 'farmer']:
        abort(403)
    # Add sales analytics logic here
    return render_template('sales_analytics.html')

@routes_bp.route('/agent/analytics/regional')
@login_required
def regional_analytics():
    if current_user.user_type != 'agent':
        abort(403)
    # Add regional analytics logic here
    return render_template('regional_analytics.html')

@routes_bp.route('/crop/performance')
@login_required
def crop_performance():
    if current_user.user_type != 'farmer':
        abort(403)
    # Add crop performance logic here
    return render_template('crop_performance.html')

# ================== Support System ==================
@routes_bp.route('/support')
@login_required
def support_tickets():
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).all()
    return render_template('support_tickets.html', tickets=tickets)

@routes_bp.route('/knowledge-base')
def knowledge_base():
    articles = [KnowledgeArticle(**r) for r in KnowledgeArticle.all()]
    return render_template('knowledge_base.html', articles=articles)

@routes_bp.route('/ticket/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    rows = SupportTicket.find(id=ticket_id)
    if not rows:
        abort(404)
    ticket = SupportTicket(**rows[0])
    if ticket.user_id != current_user.id and current_user.user_type != 'agent':
        abort(403)
    return render_template('ticket_detail.html', ticket=ticket)

# ================== Notification System ==================
@routes_bp.route('/notifications')
@login_required
def notifications():
    rows = Notification.find(user_id=current_user.id)
    notifications = [Notification(**r) for r in rows]
    return render_template('notifications.html', notifications=notifications)

@routes_bp.route('/alerts')
@login_required
def alert_system():
    if current_user.user_type != 'agent':
        abort(403)
    alerts = [SystemAlert(**r) for r in SystemAlert.all()]
    return render_template('alert_system.html', alerts=alerts)

# ================== GIS/Mapping Routes ==================
@routes_bp.route('/farm/map')
@login_required
def farm_map():
    if current_user.user_type != 'farmer':
        abort(403)
    return render_template('farm_map.html')

@routes_bp.route('/agent/regional-overview')
@login_required
def regional_overview():
    if current_user.user_type != 'agent':
        abort(403)
    return render_template('regional_overview.html')

# ================== Additional Helper Routes ==================
@routes_bp.route('/dashboard/sidebar')
@login_required
def get_sidebar():
    """Dynamic sidebar loader"""
    role = current_user.user_type
    return render_template(f'dashboard/{role}/sidebar.html')