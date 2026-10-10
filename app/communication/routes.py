import re
from datetime import datetime, timezone

from flask import abort, flash, redirect, render_template, session, url_for

from app.auth.decorators import role_required
from app.communication import communication_bp
from app.communication.forms import MessageForm
from app.database import commit_with_feedback
from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.intake import Intake
from app.models.message import Message
from app.models.specialty import Specialty
from app.models.user import User
from app.patient.intake_forms import IntakeForm


FLAG_PATTERNS = {
    "sex": r"\bsex(?:ual(?:ity|ly)?)?\b",
    "death": r"\bdeaths?\b",
    "kill": r"\bkill(?:s|ed|ing)?\b",
    "adoption": r"\badoption\b",
    "drugs": r"\bdrugs?\b",
    "weed": r"\bweeds?\b",
    "marijuana": r"\bmarijuana\b",
    "cannabis": r"\bcannabis\b",
}


def _flagged_terms(body):
    return [
        term for term, pattern in FLAG_PATTERNS.items()
        if re.search(pattern, body, flags=re.IGNORECASE)
    ]


def _authorize_conversation(appointment_id):
    appointment = db.get_or_404(Appointment, appointment_id)
    user = db.get_or_404(User, session["user_id"])
    if user.role == "admin":
        return appointment
    if user.role == "patient" and appointment.patient.user_id == user.id:
        return appointment
    if (
        user.role == "doctor"
        and appointment.doctor.user_id == user.id
        and not appointment.doctor.is_suspended
    ):
        return appointment
    abort(403)


@communication_bp.route("/appointments/<int:appointment_id>", methods=["GET", "POST"])
@role_required("patient", "doctor", "admin")
def conversation(appointment_id):
    appointment = _authorize_conversation(appointment_id)
    user = db.get_or_404(User, session["user_id"])
    form = MessageForm()

    if user.role != "admin" and form.validate_on_submit():
        terms = _flagged_terms(form.body.data)
        message = Message(
            appointment=appointment,
            sender=user,
            body=form.body.data.strip(),
            flagged_terms=",".join(terms) or None
        )
        db.session.add(message)
        message_success = "Message sent."
        if terms:
            message_success += (
                " It was flagged for private administrator review under the "
                "clinic's communication policy."
            )
        if commit_with_feedback(message_success):
            return redirect(
                url_for(
                    "communication.conversation",
                    appointment_id=appointment.id
                )
            )

    latest_intake = Intake.query.filter_by(
        patient_id=appointment.patient_id
    ).order_by(Intake.created_at.desc()).first()
    return render_template(
        "communication/conversation.html",
        appointment=appointment,
        messages=Message.query.filter_by(
            appointment_id=appointment.id
        ).order_by(Message.created_at.asc()).all(),
        latest_intake=latest_intake if user.role != "admin" else None,
        form=form,
        is_admin=user.role == "admin"
    )


@communication_bp.route("/intake", methods=["GET", "POST"])
@role_required("patient")
def intake():
    user = db.get_or_404(User, session["user_id"])
    if user.patient_profile is None:
        abort(403)

    form = IntakeForm()
    specialties = Specialty.query.order_by(Specialty.name).all()
    form.specialty_id.choices = [(0, "Not sure")] + [
        (item.id, item.name) for item in specialties
    ]

    suggestion = None
    if form.validate_on_submit():
        selected_specialty_id = form.specialty_id.data or None
        if selected_specialty_id:
            suggestion = Doctor.query.filter_by(
                specialty_id=selected_specialty_id,
                is_suspended=False
            ).order_by(Doctor.name).first()
        record = Intake(
            patient=user.patient_profile,
            symptoms=form.symptoms.data.strip(),
            symptom_duration=form.symptom_duration.data.strip(),
            previous_illness=(form.previous_illness.data or "").strip() or None,
            specialty_id=selected_specialty_id,
            recommended_doctor=suggestion
        )
        db.session.add(record)
        if commit_with_feedback(
            "Your intake was saved. The doctor suggestion is for confirmation, "
            "not a diagnosis."
        ):
            return render_template(
                "communication/intake_result.html",
                intake=record,
                suggestion=suggestion
            )

    return render_template("communication/intake.html", form=form)


@communication_bp.route("/admin")
@role_required("admin")
def admin_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template("admin/communications.html", messages=messages)


@communication_bp.route("/admin/messages/<int:message_id>/review", methods=["POST"])
@role_required("admin")
def review_message(message_id):
    message = db.get_or_404(Message, message_id)
    message.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    message.reviewed_by_id = session["user_id"]
    commit_with_feedback("Message marked as reviewed.")
    return redirect(url_for("communication.admin_messages"))
