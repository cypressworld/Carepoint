from datetime import datetime, timezone

from app.extensions import db


class Intake(db.Model):
    __tablename__ = "intakes"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False,
        index=True
    )
    symptoms = db.Column(db.Text, nullable=False)
    symptom_duration = db.Column(db.String(500), nullable=False)
    previous_illness = db.Column(db.Text, nullable=True)
    specialty_id = db.Column(
        db.Integer,
        db.ForeignKey("specialties.id"),
        nullable=True
    )
    recommended_doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=True
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    patient = db.relationship("Patient", backref="intakes")
    specialty = db.relationship("Specialty")
    recommended_doctor = db.relationship("Doctor")
