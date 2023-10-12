import os

from flask_uploads import UploadSet, IMAGES, configure_uploads

from models import Users, Post, db
from flask import Blueprint, render_template, session, request, flash, redirect, url_for, jsonify, send_from_directory, current_app

admin = Blueprint('admin', __name__, template_folder="templates", static_folder="static")

# Создание экземпляра UploadSet для загрузки изображений
photos = UploadSet("photos", IMAGES)


# главная страница админ-панели
@admin.route('/')
def index():
    if 'user_name' in session and 'user_id' in session and 'group' in session and session.get('group') == 1:
        print(f'сейчас в сессии записано user_name: {session.get("user_name")} метка id: {session.get("user_id")}')
    else:
        print(f'это не администратор ')
        print(session.get('group'))

    return render_template('admin/admin_index.html', title="Админ-панель")


# маршрут списка пользователей сайта
@admin.route('/users')
def users_show_all():
    if 'user_name' in session and 'user_id' in session and 'group' in session and session.get('group') == 1:
        users = Users.query.all()  # Извлекаем всех пользователей из базы данных

        return render_template('admin/admin_users.html', title="ADMIN-Пользователи сайта", users=users)
    else:
        return 'У вас нет прав для редактирования новостей!'


# маршрут перечня новостей в админ панели
@admin.route('/show-posts')
def show_posts():
    if 'user_name' in session and 'user_id' in session and 'group' in session and session.get('group') == 1:
        posts = Post.query.all()  # Извлекаем все новости с сайта

        return render_template('admin/admin_show_posts.html', title="ADMIN-Список новостей для редактирования", posts=posts)
    else:
        return 'У вас нет прав для редактирования новостей!'


# маршрут для редактирования новости
@admin.route('/edit-post/<int:post_id>', methods=['POST', 'GET'])
def edit_post(post_id):
    if 'user_name' in session and 'user_id' in session and 'group' in session and session.get('group') == 1:
        image_folder = post_id  # получаем путь к папке с изображениями
        print('image_folder', image_folder)
        post_data_edit = Post.query.filter_by(id=post_id).first()  # получаем объект с данными новости по id

        if request.method == 'GET':  # если get то передаем объект новости и его id
            ...
            return render_template('admin/admin_edit_post.html', title='ADMIN-Редактирование новости', post_data_edit=post_data_edit, image_folder=image_folder)

        if request.method == "POST":  # если post то
            print('Данные из формы: ', request.form)  # просмотр в консоли данных отправленных из формы редактора
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


# маршрут возвращает перечень путей к файлам изображений из папки новости
@admin.route('/get-images/<path:folder>')
def get_images(folder):
    # путь к папке новости (формируется для проверки папки в файловой системе)
    folder_path_system = os.path.normpath(current_app.config["BASE_DIR"] + '/' + os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], folder))
    print('Проверяем есть ли папка новости по пути folder_path_system: ', folder_path_system)
    # путь к папке новости (формируется для отправки на сторону клиента в обработку скриптом модального окна)
    folder_path = os.path.normpath('/' + os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], folder))
    print('folder_path', folder_path)
    # проверяем есть ли папка новости по пути
    if os.path.exists(folder_path_system):
        print('папка найдена')
        print('------------')

        # список с загруженными изображениями
        # ссылки формируются согласно HTML адресам (слеш /)
        # images = [os.path.normpath(os.path.join(folder_path, filename)) for filename in os.listdir(folder_path_system)]
        images = [(os.path.normpath(os.path.join(folder_path, filename))).replace('\\', '/') for filename in os.listdir(folder_path_system)]
        print('-----images---', images, len(images))
        if len(images) > 0:
            return jsonify({'images': images})
        else:
            return jsonify({'images': 'None'})
    else:
        print('такой папки нет')
        return jsonify({'images': 'None'})


# Маршрут позволяет клиенту получать доступ к статическим файлам (например, изображениям)
# которые хранятся в указанной директории UPLOADED_PHOTOS_DEST, путем запроса URL, который включает имя файла.
@admin.route('/uploads/posts/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOADED_PHOTOS_DEST'], filename)


# Обработчик для загрузки изображений
@admin.route('/upload-image/<int:post_id>', methods=['POST'])
def upload_image(post_id):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file:
        # Создаём папку с названием id новости, если она не существует
        upload_folder = os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], str(post_id))
        print('Путь для создания папки в директории если ее нет: ', upload_folder)
        if not os.path.exists(upload_folder):  # если папки нет то создаем папку
            os.makedirs(upload_folder)
            print('Папка создана по пути: ', upload_folder)

        # записываем файл в директорию новости
        filename = photos.save(file, folder=str(post_id))  # возвращает расположение файла (12/valtek.png)
        # url = os.path.normpath('/' + os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], filename))
        url = ('/' + current_app.config["UPLOADED_PHOTOS_DEST"] + '/' + filename).replace('\\', '/')
        print('url', url)
        return jsonify({'location': url}), 200


# Маршрут Добавления новости
@admin.route('/add-news', methods=['POST', 'GET'])
def add_news():
    return render_template('admin/admin_add_news.html', title="ADMIN-Добавление новости")
