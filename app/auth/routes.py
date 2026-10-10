from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    session
)

from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm
from app.extensions import db
from app.database import commit_with_feedback
from app.models.user import User
from app.models.patient import Patient


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Public registration always creates a patient; users cannot self-assign roles.
    if "user_id" in session:
        return redirect(url_for("main.index"))

    form = RegistrationForm()

    if form.validate_on_submit():

        existing_user = User.query.filter_by(
            email=form.email.data.lower().strip()
        ).first()

        if existing_user:
            flash(
                "An account with that email already exists.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

        user = User(
            email=form.email.data.lower().strip(),
            role="patient"
        )

        user.set_password(form.password.data)

        patient = Patient(
            user=user,
            name=form.name.data.strip(),
            phone=form.phone.data.strip()
        )
        db.session.add_all([user, patient])
        if not commit_with_feedback(
            "Registration successful. Please log in."
        ):
            return render_template("auth/register.html", form=form)

        return redirect(url_for("auth.login"))

    return render_template(
        "auth/register.html",
        form=form
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Clear old session data before creating a new authenticated session.
    if "user_id" in session:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():

        email = form.email.data.lower().strip()

        user = User.query.filter_by(
            email=email
        ).first()

        if user is None or not user.check_password(
            form.password.data
        ):
            flash(
                "Invalid email or password.",
                "danger"
            )
            return render_template("auth/login.html", form=form)

        if user.role == "doctor" and (
            user.doctor_profile is None or user.doctor_profile.is_suspended
        ):
            flash(
                "This doctor account is unavailable. Contact the clinic administrator.",
                "danger"
            )
            return render_template("auth/login.html", form=form)

        session.clear()

        session["user_id"] = user.id
        session["role"] = user.role

        if user.role == "patient":
            return redirect(
                url_for("patient.dashboard")
            )

        if user.role == "doctor":
            return redirect(
                url_for("doctor.dashboard")
            )

        if user.role == "admin":
            return redirect(
                url_for("admin.dashboard")
            )

        session.clear()

        flash(
            "Invalid account role.",
            "danger"
        )

        return redirect(url_for("auth.login"))

    return render_template(
        "auth/login.html",
        form=form
    )
    
@auth_bp.route("/logout", methods=["POST"])
def logout():
    # Logout changes authentication state, so it is a CSRF-protected POST.
    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )