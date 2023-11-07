""" Файл настроек для приложения app.py"""
import secrets
import os

# Путь к корню проекта относительно расположения файла в котором исполняется код ниже:
# то есть если файл будет перемещён и выполнен скрипт, то корень будет записан относительно данного файла...
# файл config не перемещать !!!!
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# указываем путь к базе данных ( для подключения посредством docker)
# mysql это название имени сервиса из docker-compouse-development.yml
SQLALCHEMY_DATABASE_URI = 'mysql://root:root@mysql:3306/db_flask'

# Генерация ключа
SECRET_KEY = secrets.token_hex(16)
# Режим отладки
DEBUG = True
# Папка куда будут сохраняться изображения ( os.path.join('uploads', 'posts')
# такой формат используется для адаптации путей под разные ОС )
UPLOADED_PHOTOS_DEST = os.path.join('static', 'uploads', 'posts')

JSON_AS_ASCII = False

