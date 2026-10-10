from datetime import datetime, timedelta

from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.intake import Intake
from app.models.message import Message
from app.models.patient import Patient
from app.models.specialty import Specialty
from app.models.user import User


def create_patient(email="patient@example.com"):
    user = User(email=email, role="patient")
    user.set_password("LongEnoughPassword42")
    patient = Patient(user=user, name="Pat Example", phone="555-0101")
    db.session.add_all([user, patient])
    return user, patient


def create_doctor(email="doctor@example.com", specialty=None):
    user = User(email=email, role="doctor")
    user.set_password("LongEnoughPassword42")
    doctor = Doctor(user=user, name="Dr. Example", specialty=specialty)
    db.session.add_all([user, doctor])
    return user, doctor


def sign_in(client, user_id, role):
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["role"] = role


def test_patient_intake_saves_history_and_suggests_matching_doctor(client, app):
    with app.app_context():
        user, _ = create_patient()
        specialty = Specialty(name="Family Medicine")
        db.session.add(specialty)
        db.session.flush()
        _, doctor = create_doctor(specialty=specialty)
        db.session.commit()
        user_id = user.id
        doctor_name = doctor.name
        specialty_id = specialty.id

    sign_in(client, user_id, "patient")
    response = client.post(
        "/communication/intake",
        data={
            "symptoms": "Persistent cough",
            "symptom_duration": "One week",
            "previous_illness": "Recent flu",
            "specialty_id": str(specialty_id),
            "submit": "Save intake and get a suggestion",
        },
    )
    assert response.status_code == 200
    assert doctor_name.encode() in response.data
    assert b"not a diagnosis" in response.data
    with app.app_context():
        intake = Intake.query.one()
        assert intake.symptoms == "Persistent cough"
        assert intake.symptom_duration == "One week"
        assert intake.previous_illness == "Recent flu"
        assert intake.recommended_doctor.name == doctor_name


def test_assigned_patient_and_doctor_can_chat_and_admin_can_review(client, app):
    with app.app_context():
        patient_user, patient = create_patient()
        doctor_user, doctor = create_doctor()
        appointment = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=datetime.now() + timedelta(days=1),
            status="scheduled"
        )
        db.session.add(appointment)
        db.session.commit()
        patient_id = patient_user.id
        doctor_user_id = doctor_user.id
        appointment_id = appointment.id

    sign_in(client, patient_id, "patient")
    response = client.post(
        f"/communication/appointments/{appointment_id}",
        data={"body": "Hello doctor.", "submit": "Send message"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Message sent" in response.data
    assert b"Hello doctor." in response.data

    sign_in(client, doctor_user_id, "doctor")
    response = client.post(
        f"/communication/appointments/{appointment_id}",
        data={"body": "How long have symptoms lasted?", "submit": "Send message"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"How long have symptoms lasted?" in response.data

    with app.app_context():
        admin = User(email="admin@example.com", role="admin")
        admin.set_password("LongEnoughPassword42")
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.id

    sign_in(client, admin_id, "admin")
    response = client.get("/communication/admin")
    assert response.status_code == 200
    assert b"Hello doctor." in response.data
    with app.app_context():
        assert Message.query.count() == 2


def test_keyword_flags_are_private_review_only(client, app):
    with app.app_context():
        patient_user, patient = create_patient()
        _, doctor = create_doctor()
        appointment = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=datetime.now() + timedelta(days=1),
            status="scheduled"
        )
        db.session.add(appointment)
        db.session.commit()
        patient_id = patient_user.id
        appointment_id = appointment.id

    sign_in(client, patient_id, "patient")
    response = client.post(
        f"/communication/appointments/{appointment_id}",
        data={"body": "I am worried about death and weed.", "submit": "Send message"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"flagged for private administrator review" in response.data

    with app.app_context():
        message = Message.query.one()
        assert message.flagged_terms == "death,weed"
        assert message.reviewed_at is None
        message_id = message.id
        admin = User(email="admin@example.com", role="admin")
        admin.set_password("LongEnoughPassword42")
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.id

    sign_in(client, admin_id, "admin")
    assert client.get("/communication/admin").status_code == 200
    assert client.post(
        f"/communication/admin/messages/{message_id}/review",
        follow_redirects=True
    ).status_code == 200
    with app.app_context():
        assert Message.query.one().reviewed_at is not None


def test_doctor_cannot_open_another_doctors_conversation(client, app):
    with app.app_context():
        patient_user, patient = create_patient()
        _, assigned_doctor = create_doctor("assigned@example.com")
        other_user, other_doctor = create_doctor("other@example.com")
        appointment = Appointment(
            patient=patient,
            doctor=assigned_doctor,
            appointment_date=datetime.now() + timedelta(days=1),
            status="scheduled"
        )
        db.session.add(appointment)
        db.session.commit()
        other_user_id = other_user.id
        appointment_id = appointment.id
        assert patient_user.id

    sign_in(client, other_user_id, "doctor")
    assert client.get(
        f"/communication/appointments/{appointment_id}"
    ).status_code == 403


def test_suspended_doctor_cannot_log_in_or_receive_bookings(client, app):
    with app.app_context():
        admin = User(email="admin@example.com", role="admin")
        admin.set_password("LongEnoughPassword42")
        db.session.add(admin)
        doctor_user, doctor = create_doctor()
        db.session.commit()
        admin_id = admin.id
        doctor_user_id = doctor_user.id
        doctor_id = doctor.id

    sign_in(client, admin_id, "admin")
    response = client.post(
        f"/admin/doctors/{doctor_id}/suspension",
        data={"action": "suspend"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Doctor suspended" in response.data

    with app.app_context():
        assert db.session.get(Doctor, doctor_id).is_suspended

    with app.app_context():
        patient_user, _ = create_patient()
        db.session.commit()
        patient_id = patient_user.id
    sign_in(client, patient_id, "patient")
    future_date = (datetime.now() + timedelta(days=2)).replace(second=0, microsecond=0)
    response = client.post(
        "/patient/appointments/new",
        data={
            "doctor_id": str(doctor_id),
            "appointment_date": future_date.strftime("%Y-%m-%dT%H:%M"),
            "submit": "Request appointment",
        },
    )
    assert response.status_code == 200
    with app.app_context():
        assert Appointment.query.count() == 0

    with client.session_transaction() as session:
        session.clear()
    response = client.post(
        "/auth/login",
        data={"email": "doctor@example.com", "password": "LongEnoughPassword42"},
    )
    assert response.status_code == 200
    assert b"account is unavailable" in response.data

    sign_in(client, doctor_user_id, "doctor")
    response = client.get("/doctor/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
