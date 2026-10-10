from flask import Blueprint
from importlib import import_module

# Administrative management routes are isolated behind the admin blueprint.
admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

# Importing routes registers their URL rules on the blueprint.
import_module("app.admin.routes")