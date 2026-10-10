from app.extensions import db


class Specialty(db.Model):
    # A specialty can be shared by many doctors.
    __tablename__ = "specialties"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )
