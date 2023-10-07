"""Модуль представлений таблиц для БД"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # создаем объект SQLAlchemy


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=False)
    psw = db.Column(db.String(500), nullable=False)
    group = db.Column(db.Integer(), default=0)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    autor = db.Column(db.String(40), nullable=False, default='')
    date = db.Column(db.DateTime, nullable=False, default='2000-01-01 00:00:00')
    short_story = db.Column(db.Text, nullable=False)
    full_story = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(255), nullable=False, default='')
    descr = db.Column(db.String(300), nullable=False, default='')
    alt_name = db.Column(db.String(190), nullable=False, default='')
