""" Файл настроек для приложения app.py"""
import secrets

# указываем путь к базе данных
SQLALCHEMY_DATABASE_URI = 'mysql://root:root@localhost/db_flask'
# генерация ключа
SECRET_KEY = secrets.token_hex(16)
# режим отладки
DEBUG = True
# Папка куда будут сохраняться изображения
UPLOADED_PHOTOS_DEST = 'static/uploads/posts'

