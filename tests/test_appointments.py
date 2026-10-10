from datetime import datetime, timedelta

from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User


# These cases demonstrate booking, patient ownership, and doctor assignment checks.
def create_patient(email, name):
    user = User(email=email, role="patient")
    user.set_password("LongEnoughPassword42")
    db.session.add(user)
    db.session.flush()
    patient = Patient(user_id=user.id, name=name, phone="555-0110")
    db.session.add(patient)
    return user, patient


def create_doctor(email, name):
    user = User(email=email, role="doctor")
    user.set_password("LongEnoughPassword42")
    db.session.add(user)
    db.session.flush()
    doctor = Doctor(user_id=user.id, name=name)
    db.session.add(doctor)
    return user, doctor


def test_patient_can_book_future_appointment(client, app):
    with app.app_context():
        _, patient = create_patient("patient@example.com", "Pat Example")
        _, doctor = create_doctor("doctor@example.com", "Dr. Example")
        db.session.commit()
        patient_user_id = patient.user_id
        doctor_id = doctor.id

    with client.session_transaction() as session:
        session["user_id"] = patient_user_id
        session["role"] = "patient"

    date_value = (datetime.now() + timedelta(days=3)).replace(second=0, microsecond=0)
    response = client.post(
        "/patient/appointments/new",
        data={
            "doctor_id": str(doctor_id),
            "appointment_date": date_value.strftime("%Y-%m-%dT%H:%M"),
            "submit": "Request appointment",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"appointment has been requested" in response.data
    with app.app_context():
        appointment = Appointment.query.one()
        assert appointment.patient.user_id == patient_user_id
        assert appointment.doctor_id == doctor_id
        assert appointment.status == "scheduled"


def test_patient_cannot_book_same_doctor_time_twice(client, app):
    with app.app_context():
        _, first_patient = create_patient("first@example.com", "First Patient")
        second_user, _ = create_patient("second@example.com", "Second Patient")
        _, doctor = create_doctor("doctor@example.com", "Dr. Example")
        appointment_date = (datetime.now() + timedelta(days=3)).replace(
            second=0,
            microsecond=0
        )
        db.session.add(Appointment(
            patient=first_patient,
            doctor=doctor,
            appointment_date=appointment_date,
            status="scheduled"
        ))
        db.session.commit()
        second_user_id = second_user.id
        doctor_id = doctor.id

    with client.session_transaction() as session:
        session["user_id"] = second_user_id
        session["role"] = "patient"

    response = client.post(
        "/patient/appointments/new",
        data={
            "doctor_id": str(doctor_id),
            "appointment_date": appointment_date.strftime("%Y-%m-%dT%H:%M"),
            "submit": "Request appointment",
        },
    )
    assert response.status_code == 200
    assert b"already has an appointment" in response.data
    with app.app_context():
        assert Appointment.query.count() == 1


def test_patient_cannot_book_past_appointment(client, app):
    with app.app_context():
        patient_user, _ = create_patient("patient@example.com", "Pat Example")
        _, doctor = create_doctor("doctor@example.com", "Dr. Example")
        db.session.commit()
        patient_user_id = patient_user.id
        doctor_id = doctor.id

    with client.session_transaction() as session:
        session["user_id"] = patient_user_id
        session["role"] = "patient"

    past_date = (datetime.now() - timedelta(days=1)).replace(second=0, microsecond=0)
    response = client.post(
        "/patient/appointments/new",
        data={
            "doctor_id": str(doctor_id),
            "appointment_date": past_date.strftime("%Y-%m-%dT%H:%M"),
            "submit": "Request appointment",
        },
    )
    assert response.status_code == 200
    assert b"Choose a date and time in the future" in response.data
    with app.app_context():
        assert Appointment.query.count() == 0


def test_patient_cannot_view_another_patients_appointment(client, app):
    with app.app_context():
        _, owner = create_patient("owner@example.com", "Owner Patient")
        other_user, _ = create_patient("other@example.com", "Other Patient")
        _, doctor = create_doctor("doctor@example.com", "Dr. Example")
        appointment = Appointment(
            patient=owner,
            doctor=doctor,
            appointment_date=datetime.now() + timedelta(days=1),
            status="scheduled",
        )
        db.session.add(appointment)
        db.session.commit()
        appointment_id = appointment.id
        other_user_id = other_user.id

    with client.session_transaction() as session:
        session["user_id"] = other_user_id
        session["role"] = "patient"

    assert client.get(f"/patient/appointments/{appointment_id}").status_code == 403


def test_doctor_can_update_only_assigned_appointment(client, app):
    with app.app_context():
        _, patient = create_patient("patient@example.com", "Pat Example")
        doctor_user, doctor = create_doctor("doctor@example.com", "Dr. Example")
        _, other_doctor = create_doctor("other-doctor@example.com", "Dr. Other")
        appointment = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=datetime.now() + timedelta(days=1),
            status="scheduled",
        )
        other_appointment = Appointment(
            patient=patient,
            doctor=other_doctor,
            appointment_date=datetime.now() + timedelta(days=2),
            status="scheduled",
        )
        db.session.add_all([appointment, other_appointment])
        db.session.commit()
        doctor_user_id = doctor_user.id
        appointment_id = appointment.id
        other_appointment_id = other_appointment.id

    with client.session_transaction() as session:
        session["user_id"] = doctor_user_id
        session["role"] = "doctor"

    response = client.post(
        f"/doctor/appointments/{appointment_id}/status",
        data={"status": "confirmed"},
    )
    assert response.status_code == 302
    assert client.post(
        f"/doctor/appointments/{other_appointment_id}/status",
        data={"status": "completed"},
    ).status_code == 403

    with app.app_context():
        assert db.session.get(Appointment, appointment_id).status == "confirmed"
        assert db.session.get(Appointment, other_appointment_id).status == "scheduled"


def test_doctor_cannot_submit_unknown_status(client, app):
    with app.app_context():
        _, patient = create_patient("patient@example.com", "Pat Example")
        doctor_user, doctor = create_doctor("doctor@example.com", "Dr. Example")
        appointment = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=datetime.now() + timedelta(days=1),
            status="scheduled",
        )
        db.session.add(appointment)
        db.session.commit()
        doctor_user_id = doctor_user.id
        appointment_id = appointment.id

    with client.session_transaction() as session:
        session["user_id"] = doctor_user_id
        session["role"] = "doctor"

    assert client.post(
        f"/doctor/appointments/{appointment_id}/status",
        data={"status": "arbitrary"},
    ).status_code == 400
