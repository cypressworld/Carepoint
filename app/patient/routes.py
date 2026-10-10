from datetime import datetime

from flask import abort, flash, redirect, render_template, session, url_for

from app.patient import patient_bp
from app.auth.decorators import role_required
from app.extensions import db
from app.database import commit_with_feedback
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User
from app.patient.forms import AppointmentBookingForm


@patient_bp.route("/dashboard")
@role_required("patient")
def dashboard():
    user = db.get_or_404(User, session["user_id"])

    return render_template(
        "patient/dashboard.html",
        user=user,
        appointments=Appointment.query.join(Patient).filter(
            Patient.user_id == user.id
        ).order_by(Appointment.appointment_date).all()
    )


@patient_bp.route("/appointments/new", methods=["GET", "POST"])
@role_required("patient")
def book_appointment():
    # Dynamic choices ensure patients can book only with an existing doctor.
    form = AppointmentBookingForm()
    doctors = Doctor.query.filter_by(is_suspended=False).order_by(Doctor.name).all()
    form.doctor_id.choices = [(doctor.id, doctor.name) for doctor in doctors]

    if not doctors:
        flash("There are no doctors available for booking yet.", "warning")
        return render_template("patient/book_appointment.html", form=form)

    if form.validate_on_submit():
        appointment_date = form.appointment_date.data
        if appointment_date <= datetime.now():
            form.appointment_date.errors.append(
                "Choose a date and time in the future."
            )
        else:
            doctor = Doctor.query.filter_by(
                id=form.doctor_id.data,
                is_suspended=False
            ).with_for_update().first()
            if doctor is None:
                form.doctor_id.errors.append(
                    "That doctor is no longer available. Choose another."
                )
                return render_template(
                    "patient/book_appointment.html",
                    form=form
                )

            doctor_conflict = Appointment.query.filter_by(
                doctor_id=doctor.id,
                appointment_date=appointment_date
            ).filter(
                Appointment.status != "cancelled"
            ).with_for_update().first()
            if doctor_conflict:
                form.appointment_date.errors.append(
                    "That doctor already has an appointment at this date and time."
                )
                return render_template(
                    "patient/book_appointment.html",
                    form=form
                )

            user = db.get_or_404(User, session["user_id"])
            patient = user.patient_profile
            if patient is None:
                abort(403)
            patient = Patient.query.filter_by(
                id=patient.id
            ).with_for_update().first()
            if patient is None:
                abort(403)
            patient_conflict = Appointment.query.filter_by(
                patient_id=patient.id,
                appointment_date=appointment_date
            ).filter(
                Appointment.status != "cancelled"
            ).with_for_update().first()
            if patient_conflict:
                form.appointment_date.errors.append(
                    "You already have an appointment at this date and time."
                )
                return render_template(
                    "patient/book_appointment.html",
                    form=form
                )

            appointment = Appointment(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                status="scheduled"
            )
            db.session.add(appointment)
            if commit_with_feedback("Your appointment has been requested."):
                return redirect(url_for("patient.dashboard"))

    return render_template("patient/book_appointment.html", form=form)


@patient_bp.route("/appointments/<int:appointment_id>")
@role_required("patient")
def appointment_detail(appointment_id):
    # Fetch first, then enforce ownership to prevent ID-based data exposure.
    appointment = db.get_or_404(Appointment, appointment_id)
    user = db.get_or_404(User, session["user_id"])
    if appointment.patient.user_id != user.id:
        abort(403)

    return render_template(
        "patient/appointment_detail.html",
        appointment=appointment
    )


@patient_bp.route("/profile")
@role_required("patient")
def profile():
    user = db.get_or_404(User, session["user_id"])
    if user.patient_profile is None:
        abort(403)
    return render_template("patient/profile.html", user=user)