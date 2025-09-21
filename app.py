from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from flask_login import LoginManager, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
import pandas as pd
import json
import requests
import os
import uuid
from functools import wraps
import openpyxl
from openpyxl import load_workbook
from pathlib import Path
from filelock import FileLock

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuration
app.config.update(
    SECRET_KEY='your-secret-key-here',  # Change for production
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='itradeafrika@gmail.com',
    MAIL_PASSWORD='xxwvccxuwxjvqfow',
    EXCEL_DB_PATH='agriculture_data.xlsx',
    WEATHER_API_KEY='your-weather-api-key',
    IOT_API_KEY='your-iot-api-key'
)

mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class FarmRegistrationForm(FlaskForm):
    farm_name = StringField('Farm Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    farm_type = SelectField('Farm Type',
                            choices=[('crop', 'Crop'), ('livestock', 'Livestock'), ('mixed', 'Mixed')],
                            validators=[DataRequired()])
    submit = SubmitField('Register Farm')

# -------------------------------
# Excel Initialization & Helpers
# -------------------------------
EXCEL_SHEETS = {
    "users": [
        "id",               # unique user ID (UUID)
        "username",         # login name
        "email",            # contact email
        "password",         # hashed password
        "status",           # active/inactive/suspended
        "role",             # admin/agent/farmer
        "district",         # optional region/district
        "last_login",       # last login timestamp
        "farm_id"           # optional link to primary farm
    ],
    "farms": [
        "id",               # unique farm ID (UUID)
        "name",             # farm name
        "location",         # farm location
        "size",             # size in hectares/acres
        "main_crop",        # primary crop
        "soil_type",        # soil type
        "irrigation",       # irrigation type
        "owner_id",         # linked to users.id
        "created_at",       # creation timestamp
        "updated_at"        # last update timestamp
    ],
    "sensors": [
        "id",               # unique sensor ID
        "farm_id",          # linked to farms.id
        "sensor_type",      # type of sensor (temperature, soil, etc.)
        "last_reading",     # latest sensor data (JSON/string)
        "last_updated",     # timestamp of last update
        "status"            # active/inactive/error
    ],
    "preferences": [
        "id",                   # unique preference record ID
        "user_id",              # linked to users.id
        "preferred_units",       # metric/imperial
        "alert_thresholds",      # JSON thresholds for alerts
        "notification_prefs",    # email/SMS/push
        "updated_at"             # last update timestamp
    ],
    "reports": [
        "id",               # unique report ID
        "farm_id",          # linked to farms.id
        "report_type",      # e.g., compliance, yield, soil
        "data",             # report data (JSON or text)
        "status",           # draft/submitted/approved/rejected
        "created_by",       # linked to users.id
        "created_at",       # creation timestamp
        "reviewed_at"       # optional timestamp for review
    ],
    "alerts": [
        "id",               # unique alert ID
        "farm_id",          # optional link to farms.id
        "message",          # alert message
        "level",            # info/warning/critical
        "status",           # active/resolved
        "created_at"        # timestamp
    ],
    "compliance": [
        "id",               # unique compliance record ID
        "farm_id",          # linked to farms.id
        "score",            # numeric score (0–100)
        "status",           # compliant/non-compliant/pending
        "review_date",      # last reviewed date
        "reviewed_by"       # linked to users.id (agent/admin)
    ],
    "inspections": [
        "id",               # unique inspection ID
        "farm_id",          # linked to farms.id
        "type",             # inspection type
        "scheduled_date",   # planned inspection date
        "status",           # pending/completed/cancelled
        "assigned_to",      # linked to users.id (inspector)
        "created_at",       # when it was scheduled
        "completed_at"      # when inspection was done
    ]
}


def initialize_excel_file():
    """Create or recreate Excel file with proper structure."""
    try:
        db_path = Path(app.config['EXCEL_DB_PATH'])
        db_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(db_path, engine="openpyxl", mode="w") as writer:
            for sheet, columns in EXCEL_SHEETS.items():
                pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet, index=False)

        print("✅ Excel database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing Excel file: {e}")
        return False


def verify_excel_structure():
    """Ensure Excel file has required sheets and columns without wiping existing data."""
    db_path = Path(app.config['EXCEL_DB_PATH'])
    if not db_path.exists():
        return initialize_excel_file()

    repaired = False
    try:
        with pd.ExcelFile(db_path, engine="openpyxl") as xls:
            existing_sheets = xls.sheet_names

        # Open in append mode to add/replace sheets
        with pd.ExcelWriter(db_path, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
            for sheet, columns in EXCEL_SHEETS.items():
                if sheet not in existing_sheets:
                    print(f"⚠️ Adding missing sheet: {sheet}")
                    pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet, index=False)
                    repaired = True
                else:
                    df = pd.read_excel(db_path, sheet_name=sheet, engine="openpyxl")
                    missing_cols = [c for c in columns if c not in df.columns]
                    if missing_cols:
                        print(f"⚠️ Adding missing columns in '{sheet}': {missing_cols}")
                        for col in missing_cols:
                            df[col] = ""
                        df.to_excel(writer, sheet_name=sheet, index=False)
                        repaired = True

        if repaired:
            print("✅ Excel structure patched successfully")
        return True

    except Exception as e:
        print(f"❌ Error verifying Excel structure: {e}")
        return initialize_excel_file()


def get_excel_data(sheet_name):
    """Read Excel data safely."""
    try:
        if not verify_excel_structure():
            raise Exception("Invalid Excel structure")
        df = pd.read_excel(
            app.config["EXCEL_DB_PATH"],
            sheet_name=sheet_name,
            engine="openpyxl",
            dtype=str
        ).fillna("")

        # Ensure all required columns exist
        required_cols = EXCEL_SHEETS.get(sheet_name, [])
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        return df[required_cols]  # keep column order consistent
    except Exception as e:
        print(f"❌ Error reading {sheet_name}: {e}")
        return pd.DataFrame(columns=EXCEL_SHEETS.get(sheet_name, []))


def update_excel_sheet(sheet_name, data):
    """Update a sheet safely (overwrite)."""
    lock_path = str(Path(app.config["EXCEL_DB_PATH"])) + ".lock"
    try:
        with FileLock(lock_path, timeout=10):
            # Normalize datetimes
            for col in data.columns:
                if pd.api.types.is_datetime64_any_dtype(data[col]):
                    data[col] = data[col].dt.strftime("%Y-%m-%d %H:%M:%S")

            with pd.ExcelWriter(
                app.config["EXCEL_DB_PATH"],
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace"
            ) as writer:
                data.to_excel(writer, sheet_name=sheet_name, index=False)
        return True
    except Exception as e:
        print(f"❌ Error updating {sheet_name}: {e}")
        return False

# -------------------------------
# User Management
# -------------------------------

def add_user_to_excel(user_data):
    """Add a new user to Excel."""
    try:
        users = get_excel_data("users")
        user_id = str(uuid.uuid4())

        new_user = pd.DataFrame([{
            "id": user_id,
            "username": user_data["username"],
            "email": user_data["email"],
            "password": generate_password_hash(user_data["password"]),
            "status": user_data.get("status", "active"),
            "role": user_data.get("role", "farmer"),
            "district": user_data.get("district", ""),
            "last_login": None,
            "farm_id": None,
        }])

        updated_users = pd.concat([users, new_user], ignore_index=True)
        return user_id if update_excel_sheet("users", updated_users) else None
    except Exception as e:
        print(f"❌ Error adding user: {e}")
        return None


def get_user_by_username(username):
    users = get_excel_data("users")
    if users.empty or "username" not in users.columns:
        return None
    user = users[users["username"] == username].to_dict("records")
    return user[0] if user else None


def get_user_by_id(user_id):
    users = get_excel_data("users")
    user = users[users["id"] == user_id].to_dict("records")
    return user[0] if user else None


def update_user(user_id, updates):
    """Update user safely."""
    try:
        users = get_excel_data("users")
        idx = users.index[users["id"] == user_id].tolist()
        if not idx:
            return False
        for k, v in updates.items():
            users.at[idx[0], k] = v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v
        return update_excel_sheet("users", users)
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        return False

def update_user_profile(user_id, full_name, email):
    user = User.get(user_id)
    if user:
        user.full_name = full_name
        user.email = email
        user.save()

def update_user_password(user_id, password):
    user = User.get(user_id)
    if user:
        user.password = hash_password(password)
        user.save()

# -------------------------------
# Authentication
# -------------------------------

def login_user(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user["password"], password):
        update_user(user["id"], {"last_login": datetime.now()})
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        return True
    return False


def logout_user():
    session.pop("user_id", None)
    session.pop("role", None)


def current_user():
    return get_user_by_id(session["user_id"]) if "user_id" in session else None


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                flash("You do not have permission.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                flash("You do not have permission.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# Smart Agriculture Services
def get_farm_data(farm_id):
    """Get farm data from Excel"""
    farms = get_excel_data('farms')
    farm = farms[farms['id'] == farm_id].to_dict('records')
    return farm[0] if farm else None

def get_user_farms(user_id):
    """Get all farms owned by a user"""
    farms = get_excel_data('farms')
    return farms[farms['owner_id'] == user_id].to_dict('records')

def get_sensor_data(farm_id):
    """Get sensor data for a farm"""
    sensors = get_excel_data('sensors')
    return sensors[sensors['farm_id'] == farm_id].to_dict('records')

def update_sensor_data(sensor_id, data):
    """Update sensor data in Excel"""
    sensors = get_excel_data('sensors')
    idx = sensors.index[sensors['id'] == sensor_id].tolist()
    if idx:
        sensors.at[idx[0], 'last_reading'] = json.dumps(data)
        sensors.at[idx[0], 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_excel_sheet('sensors', sensors)
        return True
    return False

def fetch_iot_data(sensor_id):
    """Simulate fetching IoT sensor data"""
    # In a real app, this would call an actual API
    return {
        'temperature': 24.5,
        'humidity': 65,
        'soil_moisture': 42,
        'battery': 85,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def get_weather_data(location):
    """Simulate fetching weather data"""
    # In a real app, use a weather API
    return {
        'temperature': 22,
        'conditions': 'Partly Cloudy',
        'forecast': 'Sunny',
        'humidity': 60,
        'wind_speed': 12
    }

def get_market_prices(crop):
    """Simulate fetching market prices"""
    # In a real app, use an agricultural market API
    prices = {
        'maize': 3200,
        'wheat': 3500,
        'sunflower': 3800,
        'soybean': 4000
    }
    return prices.get(crop.lower(), 0)

def calculate_compliance_rate():
    """Calculate overall compliance rate from Excel data"""
    compliance = get_excel_data('compliance')
    if len(compliance) == 0:
        return 0
    return int(compliance['score'].mean())

def get_pending_inspections_count():
    """Count pending inspections with proper error handling"""
    try:
        inspections = get_excel_data('inspections')
        
        # Check if DataFrame is empty or missing 'status' column
        if inspections.empty or 'status' not in inspections.columns:
            return 0
            
        return len(inspections[inspections['status'].str.strip().str.lower() == 'pending'])
    except Exception as e:
        print(f"Error counting pending inspections: {e}")
        return 0

def initialize_excel_file():
    """Create or recreate Excel file with proper structure"""
    try:
        # Create directory if it doesn't exist
        Path(app.config['EXCEL_DB_PATH']).parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(
            app.config['EXCEL_DB_PATH'],
            engine='openpyxl',
            mode='w'  # Overwrite if exists
        ) as writer:
            # Users sheet
            pd.DataFrame(columns=[
                'id', 'username', 'email', 'password', 'status', 'role', 
                'district', 'last_login', 'farm_id'
            ]).to_excel(writer, sheet_name='users', index=False)
            
            # Farms sheet
            pd.DataFrame(columns=[
                'id', 'name', 'location', 'size', 'main_crop', 
                'soil_type', 'irrigation', 'owner_id'
            ]).to_excel(writer, sheet_name='farms', index=False)
            
            # Sensors sheet
            pd.DataFrame(columns=[
                'id', 'farm_id', 'sensor_type', 'last_reading', 'last_updated'
            ]).to_excel(writer, sheet_name='sensors', index=False)
            
        print("Successfully initialized Excel database file")
        return True
    except Exception as e:
        print(f"Error initializing Excel file: {e}")
        return False

def schedule_inspection(inspection_data):
    """Add new inspection with status validation"""
    try:
        inspections = get_excel_data('inspections')
        
        new_inspection = {
            'id': str(uuid.uuid4()),
            'farm_id': inspection_data.get('farm_id'),
            'type': inspection_data.get('type'),
            'scheduled_date': inspection_data.get('date'),
            'status': 'Pending',  # Default status
            'assigned_to': inspection_data.get('inspector'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Validate required fields
        if not all(new_inspection.values()):
            raise ValueError("Missing required inspection data")
            
        updated_inspections = pd.concat([
            inspections,
            pd.DataFrame([new_inspection])
        ], ignore_index=True)
        
        if update_excel_sheet('inspections', updated_inspections):
            return True
        return False
        
    except Exception as e:
        print(f"Error scheduling inspection: {e}")
        return False

def roles_required(*roles):
    """Allow access if user role is in the given roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Authentication Routes
@app.route('/')
def index():
    user = current_user()
    if not user:
        return render_template('index.html')
    
    if user['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif user['role'] == 'agent':
        return redirect(url_for('agent_dashboard'))
    elif user['role'] == 'farmer':
        return redirect(url_for('farmer_dashboard'))
    
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if login_user(username, password):
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/farmer/logout', methods=['POST'])
@login_required
def farmer_logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'farmer')
        
        if not all([username, email, password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
            
        if not verify_excel_structure():
            flash('System configuration error. Please try again later.', 'danger')
            return redirect(url_for('register'))
            
        try:
            if get_user_by_username(username):
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))
                
            user_id = add_user_to_excel({
                'username': username,
                'email': email,
                'password': password,
                'role': role
            })
            
            if user_id:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
                
        except Exception as e:
            print(f"Registration error: {e}")
            flash('An error occurred during registration', 'danger')
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# Farmer Dashboard Routes
@app.route('/farmer/dashboard', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def farmer_dashboard():
    try:
        user = current_user()
        farms = get_user_farms(user['id'])
        farm = farms[0] if farms else None
        farm_id = farm.get('id') if farm else None
        
        if not farms:
            flash('You have no farms registered yet.', 'info')
            return render_template('farmer/smart_dashboard.html', 
                                   farm_id=farm_id,
                                   user=user,    
                                   farms=[],
                                   farm=None,
                                   weather={}, 
                                   market={},
                                   iot_data={},
                                   sensors=[])

        farm = farms[0]
        weather = get_weather_data(farm['location'])
        market = {
            'main_crop': farm['main_crop'],
            'price': get_market_prices(farm['main_crop'])
        }
        sensors = get_sensor_data(farm['id'])
        iot_data = {}

        for sensor in sensors:
            iot_data[sensor['type']] = {
                'value': sensor['value'],
                'unit': sensor['unit'],
                'last_updated': sensor['last_updated'],
                'status': sensor['status']
            }

        return render_template('farmer/smart_dashboard.html',
                               farm=farm,
                               farms=farms,
                               weather=weather,
                               market=market,
                               iot_data=iot_data,
                               sensors=sensors)

    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        flash('An error occurred while loading dashboard data', 'error')
        return render_template('farmer/smart_dashboard.html',
                               user=user,   
                               farms=[],
                               farm=None,
                               weather={},
                               market={},
                               iot_data={},
                               sensors=[])


@app.route('/farmer/farm/<farm_id>')
@login_required
@role_required('farmer')
def farm_details(farm_id):
    user = current_user()
    farm = get_farm_data(farm_id)
    
    if not farm or farm['owner_id'] != user['id']:
        flash('Farm not found or access denied', 'danger')
        return redirect(url_for('farmer_dashboard'))
    
    return render_template('farmer/farm_details.html', farm=farm)

# SENSORS
@app.route('/farmer/sensors', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def sensors():
    user = current_user()
    farms = get_user_farms(user['id'])
    farm = farms[0] if farms else None

    sensor_data = get_sensor_data(farm['id']) if farm else []
    iot_data = {}  # fallback empty dict so template won't crash

    if request.method == 'POST':
        # handle sensor updates here
        flash('Sensor data updated successfully', 'success')
        return redirect(url_for('sensors'))

    return render_template(
        'farmer/sensors.html',
        farm=farm or {},           # ensure dict fallback
        sensors=sensor_data,
        iot_data=iot_data
    )


@app.route('/farmer/farm/<farm_id>/update_sensors', methods=['POST'])
@login_required
@role_required('farmer')
def update_sensors(farm_id):
    user = current_user()
    if not verify_farm_owner(farm_id, user['id']):
        flash('Access denied', 'danger')
        return redirect(url_for('smart_dashboard'))

    # Collect form fields safely
    temperature = request.form.get('temperature')
    humidity = request.form.get('humidity')
    moisture = request.form.get('moisture')
    light = request.form.get('light')

    update_sensor_data(farm_id, temperature, humidity, moisture, light)
    flash('Sensor data updated successfully', 'success')
    return redirect(url_for('sensors'))   # redirect back to sensors page


# IRRIGATION
@app.route('/farmer/irrigation', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def irrigation():
    user = current_user()
    farms = get_user_farms(user['id'])
    farm = farms[0] if farms else None

    if request.method == 'POST':
        # handle irrigation controls here
        schedule = request.form.get('schedule')
        water_amount = request.form.get('water_amount')
        # ⬇️ Here you can add your save/update logic
        flash('Irrigation settings saved', 'success')
        return redirect(url_for('irrigation'))

    return render_template(
        'farmer/irrigation.html',
        farm=farm or {}   # avoid 'NoneType has no attribute get'
    )

@app.route('/farmer/farm/<farm_id>/update_irrigation', methods=['POST'])
@login_required
@role_required('farmer')
def update_irrigation(farm_id):
    user = current_user()
    if not verify_farm_owner(farm_id, user['id']):
        flash('Access denied', 'danger')
        return redirect(url_for('smart_dashboard'))

    irrigation_status = request.form.get('irrigation_status')
    water_volume = request.form.get('water_volume')
    update_irrigation_settings(farm_id, irrigation_status, water_volume)
    flash('Irrigation settings updated', 'success')
    return redirect(url_for('smart_dashboard'))

# PREDICTIONS
@app.route('/farmer/predictions')
@login_required
@role_required('farmer')
def predictions():
    user = current_user()
    farms = get_user_farms(user['id'])
    farm = farms[0] if farms else None
    
    # fetch AI predictions here
    ai_data = {}  
    return render_template('farmer/predictions.html', farm=farm, predictions=ai_data)

@app.route('/farmer/farm/<farm_id>/update_predictions', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def update_predictions(farm_id):
    user = current_user()
    if not verify_farm_owner(farm_id, user['id']):
        flash('Access denied', 'danger')
        return redirect(url_for('smart_dashboard'))

    prediction = None

    if request.method == 'POST':
        crop = request.form.get('crop')
        date_range = request.form.get('date_range')

        # 🔮 Call your AI model / logic here
        prediction = generate_yield_prediction(farm_id, crop, date_range)

        flash('Prediction generated successfully', 'success')

        return render_template(
            'farmer/predictions.html',
            farm=get_farm_by_id(farm_id),
            prediction=prediction
        )

    # For GET → show empty form
    farm = get_farm_by_id(farm_id)
    return render_template('farmer/predictions.html', farm=farm, prediction=None)


# DRONE IMAGING
@app.route('/farmer/drone')
@login_required
@role_required('farmer')
def drone():
    user = current_user()
    farms = get_user_farms(user['id'])
    farm = farms[0] if farms else None
    
    drone_data = {}  # fetch drone imaging data
    return render_template('farmer/drone.html', farm=farm, drone_data=drone_data)

@app.route('/farmer/farm/<farm_id>/update_drone', methods=['POST'])
@login_required
@role_required('farmer')
def update_drone(farm_id):
    user = current_user()
    if not verify_farm_owner(farm_id, user['id']):
        flash('Access denied', 'danger')
        return redirect(url_for('drone'))

    vegetation_health = request.form.get('vegetation_health')
    issues_detected = request.form.get('issues_detected')

    save_drone_data(farm_id, vegetation_health, issues_detected)
    flash('Drone data submitted successfully', 'success')
    return redirect(url_for('drone'))

@app.route('/farmer/farm/<farm_id>/upload_drone_image', methods=['POST'])
@login_required
@role_required('farmer')
def upload_drone_image(farm_id):
    user = current_user()
    if not verify_farm_owner(farm_id, user['id']):
        flash('Access denied', 'danger')
        return redirect(url_for('smart_dashboard'))

    if 'drone_image' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('drone'))

    file = request.files['drone_image']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('drone'))

    # save file logic here
    flash('Drone image uploaded successfully', 'success')
    return redirect(url_for('drone'))



# REPORTS
@app.route('/farmer/reports')
@login_required
@role_required('farmer')
def reports():
    user = current_user()
    farms = get_user_farms(user['id'])
    farm = farms[0] if farms else None
    
    reports_data = []  # fetch farm reports
    return render_template('farmer/reports.html', farm=farm, reports=reports_data)

@app.route('/farmer/farm/<farm_id>/update_reports', methods=['POST'])
@login_required
@role_required('farmer')
def update_reports(farm_id):
    user = current_user()
    if not verify_farm_owner(farm_id, user['id']):
        flash('Access denied', 'danger')
        return redirect(url_for('reports'))

    title = request.form.get('report_title')
    content = request.form.get('report_content')

    save_report(farm_id, title, content)
    flash('Report submitted successfully', 'success')
    return redirect(url_for('reports'))


# SETTINGS
@app.route('/farmer/settings', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def settings():
    user = current_user()
    
    if request.method == 'POST':
        # handle settings updates here
        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings'))
    
    return render_template('farmer/settings.html', user=user)

# UPDATE PROFILE ROUTE
@app.route('/farmer/settings/update_profile', methods=['POST'])
@login_required
@role_required('farmer')
def update_profile():
    user = current_user()

    full_name = request.form.get('full_name')
    email = request.form.get('email')

    # Save changes to your user store (Excel, DB, etc.)
    update_user_profile(user['id'], full_name, email)

    flash('Profile updated successfully', 'success')
    return redirect(url_for('settings'))


# CHANGE PASSWORD ROUTE
@app.route('/farmer/settings/change_password', methods=['POST'])
@login_required
@role_required('farmer')
def change_password():
    user = current_user()
    password = request.form.get('password')

    # Update password in your user store
    update_user_password(user['id'], password)

    flash('Password changed successfully', 'success')
    return redirect(url_for('settings'))

# Admin + Agent Shared Dashboard
@app.route('/admin/dashboard', endpoint='admin_dashboard')
@app.route('/agent/dashboard', endpoint='agent_dashboard')
@login_required
@roles_required('admin', 'agent')
def shared_dashboard():
    stats = {
        'total_farms': len(get_excel_data('farms')),
        'compliance_rate': calculate_compliance_rate(),
        'pending_inspections': get_pending_inspections_count()
    }
    alerts = get_excel_data('alerts').to_dict('records')
    return render_template('admin/agent_dashboard.html', stats=stats, alerts=alerts)


# Admin-only Users
@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    users = get_excel_data('users').to_dict('records')
    return render_template('admin/users.html', users=users)


# Admin + Agent Shared Farms
@app.route('/admin/farms', endpoint='admin_farms')
@app.route('/agent/farms', endpoint='agent_farms')
@login_required
@roles_required('admin', 'agent')
def shared_farms():
    farms = get_excel_data('farms').to_dict('records')
    users = get_excel_data('users').to_dict('records')
    user_map = {u['id']: u['username'] for u in users}
    for farm in farms:
        farm['owner_name'] = user_map.get(farm['owner_id'], 'None')
    return render_template('agent/farms.html', farms=farms)


# Admin + Agent Shared Farm Detail
@app.route('/admin/farm/<farm_id>', endpoint='admin_farm_detail')
@app.route('/agent/farm/<farm_id>', endpoint='agent_farm_detail')
@login_required
@roles_required('admin', 'agent')
def shared_farm_detail(farm_id):
    farm = get_farm_data(farm_id)
    owner = get_user_by_id(farm['owner_id']) if farm else None
    compliance = get_compliance_data(farm_id)
    sensors = get_sensor_data(farm_id)

    return render_template('agent/farm_detail.html',
                           farm=farm,
                           owner=owner,
                           compliance=compliance,
                           sensors=sensors)


# Farmer Farm Registration
@app.route('/farms/register', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def farm_registration():
    form = FarmRegistrationForm()
    if form.validate_on_submit():
        farm_data = {
            "id": str(uuid.uuid4()),
            "name": form.farm_name.data,
            "location": form.location.data,
            "size": "",
            "main_crop": "",
            "soil_type": "",
            "irrigation": "",
            "owner_id": session.get('user_id')
        }
        farms = get_excel_data("farms")
        updated_farms = pd.concat([farms, pd.DataFrame([farm_data])], ignore_index=True)
        update_excel_sheet("farms", updated_farms)
        flash("Farm registered successfully!", "success")
        return redirect(url_for("farmer_dashboard"))
    return render_template("farm_registration.html", form=form)


# Admin + Agent Shared Compliance
@app.route('/admin/compliance', endpoint='admin_compliance')
@app.route('/agent/compliance', endpoint='agent_compliance')
@login_required
@roles_required('admin', 'agent')
def shared_compliance():
    compliance_data = get_excel_data('compliance').to_dict('records')
    return render_template('agent/compliance.html', records=compliance_data)


# Admin + Agent Shared Inspections
@app.route('/admin/inspections', endpoint='admin_inspections')
@app.route('/agent/inspections', endpoint='agent_inspections')
@login_required
@roles_required('admin', 'agent')
def shared_inspections():
    inspections = get_excel_data('inspections').to_dict('records')
    return render_template('agent/inspections.html', inspections=inspections)


# New Inspection (generic)
@app.route('/inspections/new', methods=['GET', 'POST'])
def new_inspection():
    return render_template('new_inspection.html')


# Admin + Agent Shared Reports
@app.route('/admin/reports', endpoint='admin_reports')
@app.route('/agent/reports', endpoint='agent_reports')
@login_required
@roles_required('admin', 'agent')
def shared_reports():
    reports = get_excel_data('reports').to_dict('records')
    return render_template('agent/reports.html', reports=reports)


# API Endpoints
@app.route('/api/sensor/<sensor_id>')
@login_required
def get_sensor_api(sensor_id):
    sensors = get_excel_data('sensors')
    sensor = sensors[sensors['id'] == sensor_id].to_dict('records')
    if not sensor:
        return jsonify({'error': 'Sensor not found'}), 404
    
    sensor = sensor[0]
    farm = get_farm_data(sensor['farm_id'])
    user = current_user()
    
    if user['role'] != 'admin' and farm['owner_id'] != user['id']:
        return jsonify({'error': 'Access denied'}), 403
    
    last_updated = datetime.strptime(sensor['last_updated'], '%Y-%m-%d %H:%M:%S') if sensor['last_updated'] else None
    if not last_updated or (datetime.now() - last_updated) > timedelta(minutes=5):
        new_data = fetch_iot_data(sensor_id)
        update_sensor_data(sensor_id, new_data)
        sensor['last_reading'] = new_data
    
    return jsonify({'sensor': sensor, 'farm': farm})

@app.route('/api/weather/<location>')
@login_required
def get_weather_api(location):
    return jsonify(get_weather_data(location))


@app.route('/api/market/<crop>')
def get_market_api(crop):
    return jsonify({'crop': crop, 'price': get_market_prices(crop)})

@app.route('/api/farm/<farm_id>/sensors', endpoint='get_farm_sensors')
@login_required
def get_farm_sensors(farm_id):
    sensors = get_excel_data('sensors')
    farm_sensors = sensors[sensors['farm_id'] == farm_id].to_dict('records')
    return jsonify({'sensors': farm_sensors})


@app.route('/submit-report', methods=['POST'])
@login_required
def submit_report():
    report_data = {
        'id': str(uuid.uuid4()),
        'type': request.form.get('report_type'),
        'content': request.form.get('content'),
        'created_by': current_user()['id'],
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'Pending Review'
    }
    reports = get_excel_data('reports')
    updated_reports = pd.concat([reports, pd.DataFrame([report_data])], ignore_index=True)
    update_excel_sheet('reports', updated_reports)
    flash('Report submitted successfully!', 'success')
    return redirect(url_for('agent_reports'))

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == '__main__':
    # Create Excel file if it doesn't exist
    if not Path(app.config['EXCEL_DB_PATH']).exists():
        with pd.ExcelWriter(app.config['EXCEL_DB_PATH'], engine='openpyxl') as writer:
            # Initialize sheets as shown in Part 1
            pass
    
    app.run(debug=True)