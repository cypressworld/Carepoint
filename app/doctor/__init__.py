from flask import Blueprint
from importlib import import_module

# Doctor routes are grouped so role checks are easy to audit by URL area.
doctor_bp = Blueprint(
    "doctor",
    __name__,
    url_prefix="/doctor"
)

# Importing routes registers their URL rules on the blueprint.
import_module("app.doctor.routes")