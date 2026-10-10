from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class IntakeForm(FlaskForm):
    symptoms = TextAreaField(
        "What symptoms or concerns would you like help with?",
        validators=[DataRequired(), Length(max=2000)]
    )
    symptom_duration = TextAreaField(
        "How long have you had this concern?",
        validators=[DataRequired(), Length(max=500)]
    )
    previous_illness = TextAreaField(
        "What was your most recent significant illness or sickness?",
        validators=[Optional(), Length(max=2000)]
    )
    specialty_id = SelectField(
        "Which type of care seems relevant? Choose “Not sure” if unsure.",
        coerce=int,
        validators=[Optional()]
    )
    submit = SubmitField("Save intake and get a suggestion")
