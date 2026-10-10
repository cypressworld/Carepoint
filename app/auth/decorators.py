from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    flash,
)

from app.extensions import db
from app.models.user import User


def login_required(view):
    # Authentication checks that a session identifies a signed-in account.
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please log in to continue.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        return view(*args, **kwargs)

    return wrapped_view


def role_required(*allowed_roles):
    # Authorization checks the role again on the server for every protected URL.
    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            user_id = session.get("user_id")
            if user_id is None:
                flash(
                    "Please log in to continue.",
                    "warning"
                )
                return redirect(url_for("auth.login"))

            user = db.session.get(User, user_id)
            if user is None:
                session.clear()
                flash(
                    "Please log in to continue.",
                    "warning"
                )

                return redirect(
                    url_for("auth.login")
                )

            session["role"] = user.role

            if user.role == "doctor" and (
                user.doctor_profile is None or user.doctor_profile.is_suspended
            ):
                session.clear()
                flash("This doctor account is suspended.", "danger")
                return redirect(url_for("auth.login"))

            if user.role not in allowed_roles:

                flash(
                    "You are not authorized to access this page.",
                    "danger"
                )

                return redirect(
                    url_for("main.index")
                )

            return view(*args, **kwargs)

        return wrapped_view

    return decorator