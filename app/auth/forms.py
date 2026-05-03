from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from ..models import User
import re

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 100)])
    confirm = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, field):
        normalized = (field.data or '').strip()
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', normalized):
            raise ValidationError('Username can contain letters, numbers, dot, underscore, and hyphen only.')
        field.data = normalized
        if User.query.filter_by(username=normalized).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        normalized = (field.data or '').strip().lower()
        field.data = normalized
        if User.query.filter_by(email=normalized).first():
            raise ValidationError('Email already registered.')

    def validate_password(self, field):
        password = field.data or ''
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must include at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must include at least one lowercase letter.')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must include at least one number.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(8, 100)])
    confirm = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Reset Password')
    
    def validate_password(self, field):
        password = field.data or ''
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must include at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must include at least one lowercase letter.')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must include at least one number.')