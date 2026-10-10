# Importing model classes here ensures migrations discover the full schema.
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.specialty import Specialty
from app.models.appointment import Appointment
from app.models.intake import Intake
from app.models.message import Message

__all__ = ["User", "Patient", "Doctor", "Specialty", "Appointment", "Intake", "Message"]