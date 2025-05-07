from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FileField, SubmitField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class ManageStudentsForm(FlaskForm):
    educational_level = SelectField('Educational Level', choices=[], validators=[DataRequired()])
    grade_name = StringField('Grade Name', validators=[Optional()])
    stream_name = StringField('Stream Name', validators=[Optional()])
    grade_id = SelectField('Grade', choices=[], validators=[Optional()])
    name = StringField('Student Name', validators=[Optional()])
    admission_number = StringField('Admission Number', validators=[Optional()])
    stream = SelectField('Stream', choices=[], validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female')], validators=[Optional()])
    student_file = FileField('Upload Students File', validators=[Optional()])
    action = HiddenField('Action')
    submit = SubmitField('Submit')
