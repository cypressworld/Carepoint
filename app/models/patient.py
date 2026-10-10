from app.extensions import db


class Patient(db.Model):
    # Patient details live apart from the User account used to authenticate.
    __tablename__ = "patients"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "patient_profile",
            uselist=False
        )
    )
