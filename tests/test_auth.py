from app.extensions import db
from app.models.patient import Patient
from app.models.user import User


# These tests show registration creates a profile and stores only a password hash.
def test_registration_creates_patient_profile_and_hashes_password(client, app):
    response = client.post(
        "/auth/register",
        data={
            "name": "Avery Patient",
            "email": "AVERY@example.com",
            "phone": "555-0100",
            "password": "LongEnoughPassword42",
            "password_confirmation": "LongEnoughPassword42",
            "submit": "Register",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Registration successful" in response.data
    with app.app_context():
        user = User.query.filter_by(email="avery@example.com").one()
        assert user.role == "patient"
        assert user.password_hash != "LongEnoughPassword42"
        assert user.check_password("LongEnoughPassword42")
        assert Patient.query.filter_by(user_id=user.id).one().name == "Avery Patient"


def test_login_and_post_logout(client, app):
    with app.app_context():
        user = User(email="patient@example.com", role="patient")
        user.set_password("LongEnoughPassword42")
        db.session.add(user)
        db.session.flush()
        db.session.add(Patient(user_id=user.id, name="Pat Example", phone="555-0101"))
        db.session.commit()

    response = client.post(
        "/auth/login",
        data={
            "email": "patient@example.com",
            "password": "LongEnoughPassword42",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/patient/dashboard")
    assert client.get("/patient/dashboard").status_code == 200

    response = client.post("/auth/logout")
    assert response.status_code == 302
    assert client.get("/patient/dashboard").status_code == 302


def test_invalid_password_does_not_create_a_session(client, app):
    with app.app_context():
        user = User(email="patient@example.com", role="patient")
        user.set_password("LongEnoughPassword42")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/auth/login",
        data={"email": "patient@example.com", "password": "WrongPassword42"},
    )
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_registration_does_not_allow_role_selection(client, app):
    client.post(
        "/auth/register",
        data={
            "name": "Morgan Patient",
            "email": "morgan@example.com",
            "phone": "555-0102",
            "password": "LongEnoughPassword42",
            "password_confirmation": "LongEnoughPassword42",
            "role": "admin",
        },
    )
    with app.app_context():
        assert User.query.filter_by(email="morgan@example.com").one().role == "patient"


def test_missing_csrf_token_is_rejected():
    from app import create_app

    class CsrfConfig:
        SECRET_KEY = "csrf-test-secret"
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        WTF_CSRF_ENABLED = True

    app = create_app(CsrfConfig)
    response = app.test_client().post("/auth/logout")
    assert response.status_code == 400
