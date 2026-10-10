from app.extensions import db


class Appointment(db.Model):
    # The foreign keys connect each booking to its patient and assigned doctor.
    __tablename__ = "appointments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    appointment_date = db.Column(
        db.DateTime,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="scheduled"
    )

    patient = db.relationship(
        "Patient",
        backref="appointments"
    )

    doctor = db.relationship(
        "Doctor",
        backref="appointments"
    )