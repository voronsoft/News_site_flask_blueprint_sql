""" Файл форм авторизации и регистрации пользователя для модуля WTF"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length


class AuthorizationForm(FlaskForm):
    email_log = StringField("*Email: ", validators=[DataRequired(), Email(message="Некорректный email")])
    pass_log = PasswordField("*Пароль: ", validators=[DataRequired(), Length(min=4, max=100, message="Пароль должен быть от 4 до 100 символов")])
    remember_me_log = BooleanField("Запомнить", default=False)
    submit = SubmitField("Войти")


class RegistrationForm(FlaskForm):
    name_reg = StringField("*Имя: ", validators=[DataRequired()])
    email_reg = StringField("*Email: ", validators=[DataRequired(), Email(message="Некорректный email")])
    password_reg = PasswordField("*Пароль: ", validators=[DataRequired(), Length(min=4, max=100, message="Пароль должен быть от 4 до 100 символов")])
    submit = SubmitField("Регистрация")
