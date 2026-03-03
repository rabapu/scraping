from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password (kosongkan untuk tidak mengubah)', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Konfirmasi Password', validators=[Optional(), EqualTo('password')])
    role = SelectField('Role', choices=[('user', 'User'), ('moderator', 'Moderator'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Simpan')

class KeywordForm(FlaskForm):
    keyword = StringField('Keyword Baru', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Tambah')

class AnalysisForm(FlaskForm):
    analysis_data = TextAreaField('Data Analisis', validators=[DataRequired(), Length(max=100000)],
        render_kw={"rows": 5, "placeholder": "Masukkan data temuan, angka, tren, dll."})
    analysis_conclusion = TextAreaField('Kesimpulan', validators=[DataRequired(), Length(max=100000)],
        render_kw={"rows": 3, "placeholder": "Kesimpulan analisis dan implikasi bagi DJBC"})
    submit = SubmitField('Simpan Analisis')
