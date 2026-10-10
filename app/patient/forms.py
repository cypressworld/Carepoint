from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired


# The browser submits a local date-time value that WTForms converts to datetime.
class AppointmentBookingForm(FlaskForm):
    doctor_id = SelectField(
        "Doctor",
        coerce=int,
        validators=[DataRequired()]
    )
    appointment_date = DateTimeLocalField(
        "Appointment date and time",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )
    submit = SubmitField("Request appointment")
