from pprint import pprint

from flask import Flask, render_template, request, url_for, flash, redirect, session, jsonify, send_from_directory
from flask_uploads import UploadSet, configure_uploads, IMAGES
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from flask_paginate import Pagination  # импорт модуля пагинации
from models import db, Users, Post  # импорт моделей представления таблиц
import config_app  # импортируем настройки для приложения
from admin.admin import admin
import os

# импорт классов WTF из файла forms.py
from forms import AuthorizationForm, RegistrationForm

# создаем приложение
app = Flask(__name__)
photos = UploadSet("photos", IMAGES)
# загружаем настройки для приложения из файла настроек
# from_object(obj) обновляет атрибуты конфигурации вашего приложения
# obj - может быть модулем(в нашем случае), классом или словарем
app.config.from_object(config_app)

configure_uploads(app, photos)

app.permanent_session_lifetime = timedelta(days=7)  # Срок жизни сессии Например, 7 дней

#  выполняет инициализацию объекта SQLAlchemy для вашего Flask-приложения
db.init_app(app)

# регистрируем admin-blueprint (!!обязательно после создания самого приложения !!)
app.register_blueprint(admin, url_prefix='/admin')


# Маршрут главная страница
@app.route('/')
def index():
    if 'user_name' in session and 'user_id' in session and "group" in session:
        return redirect(url_for('show_posts'))

    return render_template('index.html', title="Главная страница")


# ____________ маршруты  для работы с новостями ____________

# маршрут возвращает перечень путей к файлам изображений из папки новости
@app.route('/get-images/<path:folder>')
def get_images(folder):
    folder_path = app.config["UPLOADED_PHOTOS_DEST"] + '/' + folder
    images = ['/' + folder_path + '/' + filename for filename in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, filename))]
    return jsonify({'images': images})


# Маршрут позволяет клиентам получать доступ к статическим файлам (например, изображениям)
# которые хранятся в указанной директории UPLOADED_PHOTOS_DEST, путем запроса URL, который включает имя файла.
@app.route('/uploads/posts/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)


# Обработчик для загрузки изображений
@app.route('/upload-image/<int:post_id>', methods=['POST'])
def upload_image(post_id):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file:
        # Создаём папку с названием id новости, если она не существует
        upload_folder = os.path.join(app.config["UPLOADED_PHOTOS_DEST"], str(post_id))
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        filename = photos.save(file, folder=str(post_id))
        url = '/static' + url_for('uploaded_file', filename=filename)
        print('url', url)
        return jsonify({'location': url}), 200


# Маршрут для обработки статей
# видео  на эту тему https://www.youtube.com/watch?v=Ler7PRDknTs&t=115s
@app.route('/posts/')
def show_posts():
    if 'user_name' in session and 'user_id' in session:  # если клиент авторизован то показываем
        per_page = 5
        page = request.args.get('page', type=int, default=1)

        # Запрос для получения общего количества записей
        total = Post.query.count()

        # Создаём объект пагинации
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5', outer_window=0,
                                inner_window=1)
        # Получаем данные для текущей страницы
        posts = Post.query.filter(Post.id).offset((page - 1) * per_page).limit(per_page).all()
        return render_template('posts.html', title='Статьи', posts=posts, pagination=pagination)

    return render_template('index.html', title="Главная страница")


# TODO доделать запрос сохранения данных после редактирования
# маршрут для редактирования новости
@app.route('/edit-post/<int:post_id>', methods=['POST', 'GET'])
def edit_post(post_id):
    if 'user_name' in session and 'user_id' in session and 'group' in session and session.get('group') == 1:
        image_folder = post_id  # получаем путь к папке с изображениями
        post_data_edit = Post.query.filter_by(id=post_id).first()  # получаем объект с данными новости по id

        if request.method == 'GET':  # если get то передаем объект новости и его id
            ...
            return render_template('edit_post.html', title='Редактирование новости', post_data_edit=post_data_edit, image_folder=image_folder)

        if request.method == "POST":  # если post то
            # TODO реализовать метод записи в базу данных

            print(request.form)  # просмотр в консоли данных отправленных из формы редактора
            title = request.form['title']
            alt_name_post = request.form['alt_name_post']
            full_story = request.form['editor']
            short_story = request.form['editor2']

            # если пришли новые данные по post запросу то перезаписываем данные в БД
            try:
                post_data_edit.title = title
                post_data_edit.alt_name_post = alt_name_post
                post_data_edit.full_story = full_story
                post_data_edit.short_story = short_story

                db.session.commit()
                print("Данные изменены, проверьте изменения")
            except Exception as e:
                # Обработка исключения или запись информации об ошибке
                db.session.rollback()  # Откат изменений
                flash('Ошибка при обновлении данных: ' + str(e))  # Запись информации об ошибке
                print("Ошибка при обновлении данных:", e)  # Вывод информации об ошибке в консоль

            # Перенаправление на страницу самой новости после редактирования
            return redirect(url_for('full_post', post_id=post_id))

    else:
        return 'У вас нет прав для редактирования новостей!'


# маршрут для полной новости
@app.route('/full-post/<int:post_id>', methods=['POST', 'GET'])
def full_post(post_id):
    post_data = Post.query.get(post_id)
    return render_template('full_post.html', title='Редактирование новости', post_data=post_data)


# ____________ END маршруты  для работы с новостями ____________


# ____________ маршруты  для работы с пользователями ____________
# Маршрут для авторизации на сайте
@app.route('/authorization', methods=['POST', 'GET'])
def authorization():
    form_auth = AuthorizationForm()

    if form_auth.validate_on_submit():
        user = Users.query.filter_by(email=form_auth.email_log.data).first()
        if user and check_password_hash(user.psw, form_auth.pass_log.data):
            # теперь записываем в сессию
            # необходимые метки о том что пользователь авторизован
            session['user_name'] = user.name
            session['user_id'] = user.id
            session["group"] = user.group
            print(f"чек бокс - {form_auth.remember_me_log.data}")
            if form_auth.remember_me_log.data:  # если отмечен чек бокс то
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)  # помним пользователя 7 дней
            else:
                session.permanent = False  # если не отмечен то после закрытия браузера сессия стирается

            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль')

    return render_template('authorization.html', title="Авторизация", form=form_auth)


# Маршрут для выхода из сессии
@app.route('/logout')
def logout():
    # Очищаем сессию
    session.pop('user_name', None)
    session.pop('user_id', None)
    session.pop('group', None)

    # Редирект на главную страницу или на страницу авторизации
    return redirect(url_for('authorization'))


# Маршрут для регистрации
@app.route('/registration', methods=['POST', 'GET'])
def registration():
    form = RegistrationForm()
    # проверка что такого пользователя ещё нет в бд (проверка по мылу)
    if request.method == 'POST' and Users.query.filter(Users.email == form.email_reg.data).first():
        flash(f"На сайте уже есть пользователь с таким адресом - {form.email_reg.data}")
    else:  # если нет такого пользователя то продолжаем регистрацию
        if form.validate_on_submit():  # проверка полей
            try:
                hash_psw = generate_password_hash(request.form['password_reg'])
                user = Users(name=request.form['name_reg'], email=request.form['email_reg'], psw=hash_psw)
                db.session.add(user)  # добавляем объект в сессию
                db.session.flush()  # перемещение записей из сессии в класс таблицы
                db.session.commit()  # добавляем в таблицу записи из класса

                # теперь записываем в сессию
                # необходимые метки о том что пользователь авторизован
                session['user_name'] = user.name
                session['user_id'] = user.id

            except Exception as e:
                # Обработка исключения или запись информации об ошибке
                db.session.rollback()  # Откат изменений
                flash('Ошибка при обновлении данных: ' + str(e))  # Запись информации об ошибке
                print("Ошибка при обновлении данных:", e)  # Вывод информации об ошибке в консоль

            return redirect(url_for('index'))

    return render_template('registration.html', title="Регистрация", form=form)


# ____________ END маршруты  для работы с пользователями ____________


if __name__ == '__main__':
    # app.run()
    app.run(host='0.0.0.0')
