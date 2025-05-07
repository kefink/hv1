from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()
cache = Cache(config={'CACHE_TYPE': 'simple'})
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('app.config.Config')
    
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.classteacher_login'  # Set default login view
    
    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Teacher  # Import here to avoid circular imports
        return Teacher.query.get(int(user_id))

    # Register blueprints
    from app.routes import auth, headteacher, classteacher, teacher, manage, reports
    app.register_blueprint(auth.bp)
    app.register_blueprint(headteacher.bp)
    app.register_blueprint(classteacher.bp)
    app.register_blueprint(teacher.bp)
    app.register_blueprint(manage.bp)
    app.register_blueprint(reports.bp)

    return app