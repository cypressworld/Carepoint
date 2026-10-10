from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


# Admin forms create staff profiles; passwords are optional only when editing.
class DoctorForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    specialty_id = SelectField("Specialty", coerce=int, validators=[Optional()])
    password = PasswordField(
        "Password",
        validators=[Optional(), Length(min=8, message="Use at least 8 characters.")]
    )
    submit = SubmitField("Save doctor")

    def __init__(self, is_edit=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_edit:
            self.password.validators = [
                DataRequired(),
                Length(min=8, message="Use at least 8 characters.")
            ]


class SpecialtyForm(FlaskForm):
    name = StringField(
        "Specialty name",
        validators=[DataRequired(), Length(min=2, max=100)]
    )
    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Save specialty")
