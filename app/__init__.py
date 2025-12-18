from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

from .config import config

# Extensions
db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()
bcrypt = Bcrypt()


def create_app(config_name='default'):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Login manager settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from .blueprints.auth import auth_bp
    from .blueprints.dashboard import dashboard_bp
    from .blueprints.workouts import workouts_bp
    from .blueprints.running import running_bp
    from .blueprints.recovery import recovery_bp
    from .blueprints.exercises import exercises_bp
    from .blueprints.analytics import analytics_bp
    from .blueprints.api import api_bp
    from .blueprints.planning import planning_bp
    from .blueprints.export import export_bp
    from .blueprints.templates import templates_bp
    from .blueprints.body import body_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(workouts_bp, url_prefix='/workouts')
    app.register_blueprint(running_bp, url_prefix='/running')
    app.register_blueprint(recovery_bp, url_prefix='/recovery')
    app.register_blueprint(exercises_bp, url_prefix='/exercises')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(planning_bp, url_prefix='/planning')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    app.register_blueprint(body_bp, url_prefix='/body')

    # User loader for Flask-Login
    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Offline page route
    @app.route('/offline.html')
    def offline():
        return render_template('offline.html')

    return app
