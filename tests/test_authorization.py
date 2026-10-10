from app.extensions import db
from app.models.patient import Patient
from app.models.user import User


# Requests test server-side protection directly, without relying on hidden links.
def test_anonymous_user_is_redirected_from_protected_areas(client):
    for path in (
        "/patient/dashboard",
        "/doctor/dashboard",
        "/admin/dashboard",
        "/admin/doctors",
    ):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].startswith("/auth/login")


def test_patient_cannot_open_doctor_or_admin_pages(client, app):
    with app.app_context():
        user = User(email="patient@example.com", role="patient")
        user.set_password("LongEnoughPassword42")
        db.session.add(user)
        db.session.flush()
        db.session.add(Patient(user_id=user.id, name="Pat Example", phone="555-0101"))
        db.session.commit()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "patient"

    for path in ("/doctor/dashboard", "/admin/dashboard", "/admin/doctors"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "/"


def test_admin_can_open_administration(client, app):
    with app.app_context():
        user = User(email="admin@example.com", role="admin")
        user.set_password("LongEnoughPassword42")
        db.session.add(user)
        db.session.commit()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "admin"

    assert client.get("/admin/dashboard").status_code == 200
    assert client.get("/admin/doctors").status_code == 200


def test_server_role_not_session_role_controls_admin_access(client, app):
    with app.app_context():
        user = User(email="patient@example.com", role="patient")
        user.set_password("LongEnoughPassword42")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["role"] = "admin"

    response = client.get("/admin/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
