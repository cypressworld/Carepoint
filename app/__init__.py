from flask import Flask
from importlib import import_module

from config import Config
from app.extensions import db, migrate, csrf


def create_app(config_class=Config):
    # The factory lets tests create isolated app instances with their own config.
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Importing models registers every table with SQLAlchemy and Alembic.
    import_module("app.models")

    from app.auth import auth_bp
    from app.patient import patient_bp
    from app.doctor import doctor_bp
    from app.admin import admin_bp
    from app.main import main_bp
    from app.communication import communication_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(communication_bp)

    return app
