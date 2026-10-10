import os

from app import create_app
from app.extensions import db
from app.models.user import User


# Provision the first administrator out-of-band instead of offering public admin signup.
app = create_app()


def seed_admin():
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or not password:
        raise RuntimeError("Set ADMIN_EMAIL and ADMIN_PASSWORD before running this script.")
    if len(password) < 12:
        raise RuntimeError("ADMIN_PASSWORD must contain at least 12 characters.")

    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if existing:
            if existing.role != "admin":
                raise RuntimeError("The configured email belongs to a non-admin account.")
            print("Administrator already exists.")
            return

        admin = User(email=email, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("Administrator created.")


if __name__ == "__main__":
    seed_admin()
