from app.extensions import db
from app.models.doctor import Doctor
from app.models.specialty import Specialty
from app.models.user import User


# Admin workflows create staff profiles without exposing a public role selector.
def test_admin_can_create_doctor_and_specialty(client, app):
    with app.app_context():
        admin = User(email="admin@example.com", role="admin")
        admin.set_password("LongEnoughPassword42")
        specialty = Specialty(name="Family Medicine")
        db.session.add_all([admin, specialty])
        db.session.commit()
        admin_id = admin.id
        specialty_id = specialty.id

    with client.session_transaction() as session:
        session["user_id"] = admin_id
        session["role"] = "admin"

    response = client.post(
        "/admin/doctors/new",
        data={
            "name": "Dr. Taylor",
            "email": "TAYLOR@example.com",
            "phone": "555-0120",
            "specialty_id": str(specialty_id),
            "password": "DoctorPassword42",
            "submit": "Save doctor",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Doctor account created" in response.data
    with app.app_context():
        doctor = Doctor.query.one()
        assert doctor.name == "Dr. Taylor"
        assert doctor.user.email == "taylor@example.com"
        assert doctor.user.role == "doctor"
        assert doctor.user.check_password("DoctorPassword42")


def test_patient_cannot_create_doctor(client):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "patient"
    assert client.post("/admin/doctors/new").status_code == 302


def test_admin_cannot_delete_specialty_assigned_to_doctor(client, app):
    with app.app_context():
        admin = User(email="admin@example.com", role="admin")
        admin.set_password("LongEnoughPassword42")
        doctor_user = User(email="doctor@example.com", role="doctor")
        doctor_user.set_password("LongEnoughPassword42")
        specialty = Specialty(name="Cardiology")
        db.session.add_all([admin, doctor_user, specialty])
        db.session.flush()
        doctor = Doctor(
            user_id=doctor_user.id,
            specialty_id=specialty.id,
            name="Dr. Heart"
        )
        db.session.add(doctor)
        db.session.commit()
        admin_id = admin.id
        specialty_id = specialty.id

    with client.session_transaction() as session:
        session["user_id"] = admin_id
        session["role"] = "admin"

    response = client.post(
        f"/admin/specialties/{specialty_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Remove this specialty from its doctors" in response.data
    with app.app_context():
        assert db.session.get(Specialty, specialty_id) is not None
