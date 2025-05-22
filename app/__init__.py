from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_mail import Mail

from app.models import User

csrf = CSRFProtect()
login_manager = LoginManager()
mail = Mail()

# Move date_format here so we don't import back into routes.py
def date_format(value, format="%Y-%m-%d"):
    return value.strftime(format)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Register the filter before loading templates
    app.jinja_env.filters['date_format'] = date_format

    # Initialize extensions
    csrf.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    Talisman(app, content_security_policy=None)

    @login_manager.user_loader
    def load_user(user_id):
        row = User.get_by_id(int(user_id))
        return User(**row) if row else None

    # Import and register your blueprint _after_ defining filters
    from app.routes import routes_bp
    app.register_blueprint(routes_bp)

    return app

app = create_app()
