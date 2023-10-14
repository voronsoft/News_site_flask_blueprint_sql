import os
import re
import shutil
from datetime import datetime
from unidecode import unidecode
from models import Users, Post, db
from flask_uploads import UploadSet, IMAGES, configure_uploads
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


# маршрут возвращает перечень путей к файлам изображений из папки новости для модального окна
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
        url = ('/' + current_app.config["UPLOADED_PHOTOS_DEST"] + '/' + filename).replace('\\', '/')
        print('url', url)
        return jsonify({'location': url}), 200


# ---------------------------------- маршруты для добавление новости ---------------------
# Маршрут Добавления новости
@admin.route('/add-news', methods=['POST', 'GET'])
def add_news():
    image_folder = 'temp'

    if 'user_name' in session and 'user_id' in session and 'group' in session and session.get('group') == 1:
        if request.method == 'POST' and request.form['title']:
            autor = session['user_name']  # берем имя пользователя из сессии
            # Формируем дату
            current_datetime = datetime.now()  # Получаем текущую дату и время
            # Преобразуем текущую дату и время в нужный формат
            formatted_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            date = str(formatted_date)

            short_story = request.form['short_story']  # Короткая новость
            full_story = request.form['full_story']  # Полная новость
            title = request.form['title']  # Название новости
            descr = ''  # Описание новости

            #  формируем альтернативное название от названия новости из формы или исправляем если задано название пользователем
            # из текста исключаются все спец символы только буквы и цифры допускаются
            if request.form['alt_name_post']:
                alt_name = request.form['alt_name_post'].strip().lower()  # убираем пробелы и делаем все прописными
                alt_name = unidecode(re.sub(r'-+', '-', str(re.sub(r'[^a-zA-Zа-яА-Я0-9]', ' ', alt_name).strip().replace(' ', '-'))))
            else:
                alt_name = request.form['title'].strip().lower()  # убираем пробелы и делаем все прописными
                # убираем все лишние знаки - убираем пробелы в начале и конце - заменяем пробелы на дефис - убираем лишние дефисы - приводим в порядок текст
                alt_name = unidecode(re.sub(r'-+', '-', str(re.sub(r'[^a-zA-Zа-яА-Я0-9]', ' ', alt_name).strip().replace(' ', '-'))))

            # записываем данные в БД
            try:
                post = Post(
                    autor=autor,
                    date=date,
                    short_story=short_story,
                    full_story=full_story,
                    title=title,
                    descr=descr,
                    alt_name=alt_name,
                )
                db.session.add(post)  # добавляем объект в сессию
                db.session.flush()  # перемещение записей из сессии в класс таблицы
                db.session.commit()  # добавляем в таблицу записи из класса
                print('id новой новости', post.id)

                # ##########################
                # Создаем постоянную папку для новости
                permanent_folder = os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], str(post.id))
                print('permanent_folder', permanent_folder)
                if not os.path.exists(permanent_folder):
                    os.makedirs(permanent_folder)
                    print('ПОСТОЯННАЯ папка новости создана')

                # Перемещаем файлы из временной папки в постоянную
                temp_folder = os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], 'temp')
                for filename in os.listdir(temp_folder):
                    source_path = os.path.join(temp_folder, filename)
                    print('source_path-', source_path)
                    dest_path = os.path.join(permanent_folder, filename)
                    print('dest_path-', dest_path)
                    shutil.move(source_path, dest_path)

                # Удаляем временную папку после перемещения
                shutil.rmtree(temp_folder, ignore_errors=True)
                print('Папка temp по пути uploads/post/temp, была удалена, проверьте на всякий случай )))')
                # ##########################

                # Обновляем пути к изображениям в тексте новости
                # Заменяем '/temp/' на f'/{post.id}/' в полном тексте новости и короткой новости
                full_story = full_story.replace('/temp/', f'/{post.id}/')
                short_story = short_story.replace('/temp/', f'/{post.id}/')

                # Обновляем данные в БД
                post.full_story = full_story
                post.short_story = short_story
                db.session.commit()

                # Перенаправление на новую новость
                return redirect(url_for('full_post', post_id=post.id))

            except Exception as e:
                # Обработка исключения или запись информации об ошибке
                db.session.rollback()  # Откат изменений
                flash('Ошибка при добавлении статьи: ' + str(e))  # Запись информации об ошибке
                print('Ошибка при добавлении статьи: ', e)  # Вывод информации об ошибке в консоль

    else:
        return redirect(url_for('index'))

    return render_template('admin/admin_add_news.html', title="ADMIN-Добавление новости", image_folder=image_folder)


# Маршрут для загрузки изображений во временную папку
@admin.route('/upload-temp-image', methods=['POST'])
def upload_temp_image():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file:
        # Создаём временную папку для загрузки изображений
        # Создаём папку с названием id новости, если она не существует
        temp_upload_folder = os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], str('temp'))
        print('Путь для создания временной папки в директории если ее нет: ', temp_upload_folder)
        if not os.path.exists(temp_upload_folder):  # если папки нет то создаем папку
            os.makedirs(temp_upload_folder)
            print('Папка создана по пути: ', temp_upload_folder)

        # Сохраняем файл с его оригинальным именем во временную папку
        file.save(os.path.join(temp_upload_folder, file.filename))
        # Возвращаем URL загруженного временного изображения
        url = '/' + os.path.join(temp_upload_folder, file.filename).replace('\\', '/')
        print('url', url)
        return jsonify({'location': url}), 200


# Маршрут Удаление новости
@admin.route('/delete-news/<int:post_id>', methods=['POST'])
def delete_news(post_id):
    print(f'Удаление новости id: {post_id}')
    # Получаем запись из базы данных по ID новости
    post = Post.query.get(post_id)

    try:
        # Проверяем, существует ли такая новость
        if post:
            # Удаляем папку загрузки новости
            folder_to_delete = os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], str(post.id))
            print('folder_to_delete', folder_to_delete)

            if os.path.exists(folder_to_delete):
                shutil.rmtree(folder_to_delete, ignore_errors=True)

            # Удаляем запись из базы данных
            db.session.delete(post)
            db.session.commit()

            flash('Новость удалена из БД, папка изображений новости удалена')
            return redirect(url_for('admin.show_posts'))

    except Exception as e:
        # Обработка исключения или запись информации об ошибке
        db.session.rollback()  # Откат изменений
        flash('Ошибка при удалении статьи: ' + str(e))  # Запись информации об ошибке
        print('Ошибка при удалении статьи: ', e)  # Вывод информации об ошибке в консоль

    return redirect(url_for('admin.show_posts'))
