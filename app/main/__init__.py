from flask import Blueprint
from importlib import import_module

# Public landing pages belong to a separate blueprint from authenticated areas.
main_bp = Blueprint(
    "main",
    __name__
)

# Importing routes registers their URL rules on the blueprint.
import_module("app.main.routes")