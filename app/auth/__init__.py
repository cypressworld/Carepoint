from flask import Blueprint
from importlib import import_module

# A blueprint groups routes that deal with account access.
auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)

# Importing routes registers their URL rules on the blueprint.
import_module("app.auth.routes")