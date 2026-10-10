from flask import abort, flash, redirect, render_template, request, session, url_for

from app.doctor import doctor_bp
from app.auth.decorators import role_required
from app.extensions import db
from app.database import commit_with_feedback
from app.models.appointment import Appointment
from app.models.user import User


@doctor_bp.route("/dashboard")
@role_required("doctor")
def dashboard():
    user = db.get_or_404(User, session["user_id"])
    doctor = user.doctor_profile
    if doctor is None:
        abort(403)

    return render_template(
        "doctor/dashboard.html",
        user=user,
        appointments=Appointment.query.filter_by(
            doctor_id=doctor.id
        ).order_by(Appointment.appointment_date).all()
    )


@doctor_bp.route("/appointments/<int:appointment_id>/status", methods=["POST"])
@role_required("doctor")
def update_appointment_status(appointment_id):
    # The assigned-doctor check prevents doctors from editing each other's cases.
    user = db.get_or_404(User, session["user_id"])
    doctor = user.doctor_profile
    if doctor is None:
        abort(403)

    appointment = db.get_or_404(Appointment, appointment_id)
    if appointment.doctor_id != doctor.id:
        abort(403)

    status = request.form.get("status", "")
    if status not in {"scheduled", "confirmed", "completed", "cancelled"}:
        abort(400, description="Unknown appointment status.")

    appointment.status = status
    if not commit_with_feedback("Appointment status updated."):
        return redirect(url_for("doctor.dashboard"))
    return redirect(url_for("doctor.dashboard"))