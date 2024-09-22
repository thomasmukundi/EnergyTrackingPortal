# __init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


# Initialize the database
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    # Create the Flask application
    app = Flask(__name__)

    # Configure your Flask application
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize plugins
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Flask-Login configuration
    login_manager.login_view = 'auth.login'

    # User loader callback for Flask-Login
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from auth import auth_bp
    from routes import routes_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(routes_bp)

    # Create the database
    with app.app_context():
        db.create_all()

    return app
