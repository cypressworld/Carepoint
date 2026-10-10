from flask import Blueprint
from importlib import import_module

# Patient pages and patient-owned appointment operations share this URL prefix.
patient_bp = Blueprint(
    "patient",
    __name__,
    url_prefix="/patient"
)

# Importing routes registers their URL rules on the blueprint.
import_module("app.patient.routes")