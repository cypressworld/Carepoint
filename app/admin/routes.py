from flask import flash, redirect, render_template, request, url_for

from app.admin import admin_bp
from app.auth.decorators import role_required
from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.specialty import Specialty
from app.models.user import User
from app.admin.forms import DoctorForm, SpecialtyForm
from app.database import commit_with_feedback
from app.models.message import Message


# Admin route handlers combine form validation with role checks and DB changes.
@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    return render_template(
        "admin/dashboard.html",
        doctor_count=Doctor.query.count(),
        patient_count=Patient.query.count(),
        appointment_count=Appointment.query.count(),
        specialty_count=Specialty.query.count(),
        flagged_message_count=Message.query.filter(
            Message.flagged_terms.isnot(None),
            Message.reviewed_at.is_(None)
        ).count()
    )


@admin_bp.route("/doctors")
@role_required("admin")
def doctors():
    return render_template(
        "admin/doctors.html",
        doctors=Doctor.query.order_by(Doctor.name).all()
    )


@admin_bp.route("/doctors/new", methods=["GET", "POST"])
@role_required("admin")
def create_doctor():
    form = DoctorForm()
    form.specialty_id.choices = [(0, "No specialty")] + [
        (specialty.id, specialty.name)
        for specialty in Specialty.query.order_by(Specialty.name).all()
    ]

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            form.email.errors.append("An account with this email already exists.")
        else:
            user = User(email=email, role="doctor")
            user.set_password(form.password.data)
            doctor = Doctor(
                user=user,
                name=form.name.data.strip(),
                phone=(form.phone.data or "").strip() or None,
                specialty_id=form.specialty_id.data or None
            )
            db.session.add(doctor)
            if commit_with_feedback("Doctor account created."):
                return redirect(url_for("admin.doctors"))

    return render_template("admin/doctor_form.html", form=form, heading="Add doctor")


@admin_bp.route("/doctors/<int:doctor_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_doctor(doctor_id):
    doctor = db.get_or_404(Doctor, doctor_id)
    form = DoctorForm(is_edit=True, obj=doctor)
    form.specialty_id.choices = [(0, "No specialty")] + [
        (specialty.id, specialty.name)
        for specialty in Specialty.query.order_by(Specialty.name).all()
    ]

    if not form.is_submitted():
        form.email.data = doctor.user.email
        form.specialty_id.data = doctor.specialty_id or 0
    elif form.validate_on_submit():
        email = form.email.data.strip().lower()
        duplicate = User.query.filter(
            User.email == email,
            User.id != doctor.user_id
        ).first()
        if duplicate:
            form.email.errors.append("An account with this email already exists.")
        else:
            doctor.user.email = email
            doctor.name = form.name.data.strip()
            doctor.phone = (form.phone.data or "").strip() or None
            doctor.specialty_id = form.specialty_id.data or None
            if form.password.data:
                doctor.user.set_password(form.password.data)
            if commit_with_feedback("Doctor details updated."):
                return redirect(url_for("admin.doctors"))

    return render_template(
        "admin/doctor_form.html",
        form=form,
        heading="Edit doctor"
    )


@admin_bp.route("/doctors/<int:doctor_id>/delete", methods=["POST"])
@role_required("admin")
def delete_doctor(doctor_id):
    doctor = db.get_or_404(Doctor, doctor_id)
    if Appointment.query.filter_by(doctor_id=doctor.id).first():
        flash("Reassign or cancel this doctor's appointments before removal.", "warning")
    else:
        user = doctor.user
        db.session.delete(doctor)
        db.session.delete(user)
        commit_with_feedback("Doctor account removed.")
    return redirect(url_for("admin.doctors"))


@admin_bp.route("/doctors/<int:doctor_id>/suspension", methods=["POST"])
@role_required("admin")
def set_doctor_suspension(doctor_id):
    doctor = db.get_or_404(Doctor, doctor_id)
    action = request.form.get("action")
    if action not in {"suspend", "restore"}:
        return render_template(
            "admin/doctors.html",
            doctors=Doctor.query.order_by(Doctor.name).all()
        ), 400

    doctor.is_suspended = action == "suspend"
    success_message = (
        "Doctor suspended; login and new bookings are disabled."
        if doctor.is_suspended
        else "Doctor account restored."
    )
    commit_with_feedback(success_message)
    return redirect(url_for("admin.doctors"))


@admin_bp.route("/specialties", methods=["GET", "POST"])
@role_required("admin")
def specialties():
    form = SpecialtyForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        if Specialty.query.filter_by(name=name).first():
            form.name.errors.append("This specialty already exists.")
        else:
            db.session.add(
                Specialty(name=name, description=(form.description.data or "").strip() or None)
            )
            if commit_with_feedback("Specialty added."):
                return redirect(url_for("admin.specialties"))
    return render_template(
        "admin/specialties.html",
        form=form,
        specialties=Specialty.query.order_by(Specialty.name).all()
    )


@admin_bp.route("/specialties/<int:specialty_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_specialty(specialty_id):
    specialty = db.get_or_404(Specialty, specialty_id)
    form = SpecialtyForm(obj=specialty)
    if form.validate_on_submit():
        name = form.name.data.strip()
        duplicate = Specialty.query.filter(
            Specialty.name == name,
            Specialty.id != specialty.id
        ).first()
        if duplicate:
            form.name.errors.append("This specialty already exists.")
        else:
            specialty.name = name
            specialty.description = (form.description.data or "").strip() or None
            if commit_with_feedback("Specialty updated."):
                return redirect(url_for("admin.specialties"))
    return render_template("admin/specialty_form.html", form=form, specialty=specialty)


@admin_bp.route("/specialties/<int:specialty_id>/delete", methods=["POST"])
@role_required("admin")
def delete_specialty(specialty_id):
    specialty = db.get_or_404(Specialty, specialty_id)
    if specialty.doctors:
        flash("Remove this specialty from its doctors before deleting it.", "warning")
    else:
        db.session.delete(specialty)
        commit_with_feedback("Specialty removed.")
    return redirect(url_for("admin.specialties"))


@admin_bp.route("/patients")
@role_required("admin")
def patients():
    return render_template(
        "admin/patients.html",
        patients=Patient.query.join(Patient.user).order_by(Patient.name).all()
    )


@admin_bp.route("/appointments")
@role_required("admin")
def appointments():
    return render_template(
        "admin/appointments.html",
        appointments=Appointment.query.order_by(
            Appointment.appointment_date.desc()
        ).all()
    )
