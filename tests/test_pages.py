from datetime import datetime, timedelta

from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.specialty import Specialty
from app.models.user import User


# Rendering every user-facing page catches missing templates and broken endpoints.
def test_public_patient_doctor_and_admin_pages_render(client, app):
    with app.app_context():
        patient_user = User(email="patient@example.com", role="patient")
        doctor_user = User(email="doctor@example.com", role="doctor")
        admin_user = User(email="admin@example.com", role="admin")
        for user in (patient_user, doctor_user, admin_user):
            user.set_password("LongEnoughPassword42")
        specialty = Specialty(name="Family Medicine")
        db.session.add_all([patient_user, doctor_user, admin_user, specialty])
        db.session.flush()
        patient = Patient(
            user_id=patient_user.id,
            name="Pat Example",
            phone="555-0130"
        )
        doctor = Doctor(
            user_id=doctor_user.id,
            specialty_id=specialty.id,
            name="Dr. Example",
            phone="555-0131"
        )
        db.session.add_all([patient, doctor])
        db.session.flush()
        appointment = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=datetime.now() + timedelta(days=2),
            status="scheduled"
        )
        db.session.add(appointment)
        db.session.commit()
        patient_id = patient_user.id
        doctor_id = doctor_user.id
        admin_id = admin_user.id
        doctor_profile_id = doctor.id
        specialty_id = specialty.id
        appointment_id = appointment.id

    for path in ("/", "/auth/login", "/auth/register"):
        assert client.get(path).status_code == 200

    with client.session_transaction() as session:
        session["user_id"] = patient_id
        session["role"] = "patient"
    for path in (
        "/patient/dashboard",
        "/patient/profile",
        "/patient/appointments/new",
        f"/patient/appointments/{appointment_id}",
    ):
        assert client.get(path).status_code == 200

    with client.session_transaction() as session:
        session["user_id"] = doctor_id
        session["role"] = "doctor"
    assert client.get("/doctor/dashboard").status_code == 200

    with client.session_transaction() as session:
        session["user_id"] = admin_id
        session["role"] = "admin"
    for path in (
        "/admin/dashboard",
        "/admin/doctors",
        "/admin/doctors/new",
        f"/admin/doctors/{doctor_profile_id}/edit",
        "/admin/specialties",
        f"/admin/specialties/{specialty_id}/edit",
        "/admin/patients",
        "/admin/appointments",
    ):
        assert client.get(path).status_code == 200, path
