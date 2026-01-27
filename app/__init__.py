from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "main.login"
login.login_message = None  # Disable automatic "Please log in" message

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

main_bp = Blueprint("main", __name__)
admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
)


def create_app(config_class=None):
    app = Flask(__name__)
    if config_class is None:
        from config import Config

        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)

    # Set default database URI if not provided
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        import os

        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"
        )
        # Ensure the instance folder exists
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    limiter.init_app(app)

    # Import and register blueprints
    from app import routes, models  # noqa: F401, E402

    @app.context_processor
    def inject_theme():
        from flask import request

        theme = request.cookies.get("theme", "light")
        return dict(theme=theme)

    app.register_blueprint(main_bp)

    from app.admin import routes as admin_routes  # noqa: F401, E402

    app.register_blueprint(admin_bp)

    return app
