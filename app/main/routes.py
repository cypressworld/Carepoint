from flask import render_template

from app.main import main_bp


@main_bp.route("/")
def index():
    # Keep the home page public; role-specific links are rendered in the base layout.
    return render_template("main/index.html")