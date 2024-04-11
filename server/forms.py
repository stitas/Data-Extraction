from wtforms.validators import InputRequired, Length, ValidationError, EqualTo
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf import FlaskForm
from models import User

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'Username'})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20), EqualTo('confirm_password', message='Passwords must match')], render_kw={'placeholder': 'Password'})
    confirm_password = PasswordField(render_kw={'placeholder': 'Confirm password'})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'Username'})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={'placeholder': 'Password'})
    submit = SubmitField('Login')