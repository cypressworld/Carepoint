from app.extensions import db


class Doctor(db.Model):
    # A doctor profile is separate from credentials so role data stays focused.
    __tablename__ = "doctors"

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

    specialty_id = db.Column(
        db.Integer,
        db.ForeignKey("specialties.id"),
        nullable=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    is_suspended = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "doctor_profile",
            uselist=False
        )
    )

    specialty = db.relationship(
        "Specialty",
        backref="doctors"
    )
