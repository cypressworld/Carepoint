from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

# Shared extension instances are initialized by the application factory.
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
