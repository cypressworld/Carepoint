from flask import Blueprint
from importlib import import_module

communication_bp = Blueprint("communication", __name__, url_prefix="/communication")

import_module("app.communication.routes")
