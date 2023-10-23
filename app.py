import config_app  # импортируем настройки для приложения
from admin.admin import admin
from datetime import timedelta
from models import db, Users, Post  # импорт моделей представления таблиц
from flask_paginate import Pagination  # импорт модуля пагинации
from forms import AuthorizationForm, RegistrationForm
from flask_uploads import UploadSet, configure_uploads, IMAGES
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, url_for, flash, redirect, session

# Создаем приложение
app = Flask(__name__)
# Загружаем настройки для приложения из файла настроек
app.config.from_object(config_app)
# Срок жизни сессии Например, 7 дней
app.permanent_session_lifetime = timedelta(days=7)
#
# Выполняем инициализацию объекта SQLAlchemy для Flask-приложения
db.init_app(app)

# Создание экземпляра UploadSet для загрузки изображений
photos = UploadSet("photos", IMAGES)
# Настройка загрузки файлов для приложения app
configure_uploads(app, photos)

# Регистрируем admin-blueprint (!!обязательно после создания самого приложения !!)
app.register_blueprint(admin, url_prefix='/admin')


# Маршрут главная страница
@app.route('/')
def index():
    if 'user_name' in session and 'user_id' in session and "group" in session:
        return redirect(url_for('show_posts'))

    return render_template('index.html', title="Главная страница")


# ____________ маршруты  для работы с новостями ____________
# Маршрут для обработки статей
# видео  на эту тему https://www.youtube.com/watch?v=Ler7PRDknTs&t=115s
@app.route('/posts/')
def show_posts():
    if 'user_name' in session and 'user_id' in session:  # Если клиент авторизован то показываем
        per_page = 5
        page = request.args.get('page', type=int, default=1)

        # Запрос для получения общего количества записей
        total = Post.query.count()

        # Создаём объект пагинации
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5', outer_window=0, inner_window=1)
        # Получаем данные для текущей страницы
        posts = Post.query.filter(Post.id).offset((page - 1) * per_page).limit(per_page).all()
        return render_template('posts.html', title='Статьи', posts=posts, pagination=pagination)

    return render_template('index.html', title="Главная страница")


# Маршрут полной новости
@app.route('/full-post/<int:post_id>', methods=['POST', 'GET'])
def full_post(post_id):
    if db.session.get(Post, post_id):
        # Используем Session.get() вместо Query.get() (введение после версии 2.0 >)
        post_data = db.session.get(Post, post_id)
        return render_template('full_post.html', title='Редактирование новости', post_data=post_data)
    else:
        return "Такой новости не существует на сайте!!!"


# ____________ END маршруты  для работы с новостями ____________


# ____________ Маршруты  для работы с пользователями ____________
# Маршрут для авторизации на сайте
@app.route('/authorization', methods=['POST', 'GET'])
def authorization():
    form_auth = AuthorizationForm()

    if form_auth.validate_on_submit():
        user = Users.query.filter_by(email=form_auth.email_log.data).first()
        if user and check_password_hash(user.psw, form_auth.pass_log.data):
            # Записываем в сессию необходимые метки о том что пользователь авторизован
            session['user_name'] = user.name
            session['user_id'] = user.id
            session["group"] = user.group
            print(f"чек бокс - {form_auth.remember_me_log.data}")
            if form_auth.remember_me_log.data:  # Если отмечен чек бокс то
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)  # Помним пользователя 7 дней
            else:
                session.permanent = False  # Если не отмечен то после закрытия браузера сессия стирается

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
    # Проверка что такого пользователя ещё нет в бд (проверка по мылу)
    if request.method == 'POST' and Users.query.filter(Users.email == form.email_reg.data).first():
        flash(f"На сайте уже есть пользователь с таким адресом - {form.email_reg.data}")
    else:  # Если нет такого пользователя то продолжаем регистрацию
        if form.validate_on_submit():  # Проверка полей
            try:
                hash_psw = generate_password_hash(request.form['password_reg'])
                user = Users(name=request.form['name_reg'], email=request.form['email_reg'], psw=hash_psw)
                db.session.add(user)  # Добавляем объект в сессию
                db.session.flush()  # Перемещение записей из сессии в класс таблицы
                db.session.commit()  # Добавляем в таблицу записи из класса

                # Теперь записываем в сессию необходимые метки о том что пользователь авторизован
                session['user_name'] = user.name
                session['user_id'] = user.id

            except Exception as e:
                db.session.rollback()  # Откат изменений
                flash('Ошибка при обновлении данных: ' + str(e))  # Запись информации об ошибке
                print("Ошибка при обновлении данных:", e)  # Вывод информации об ошибке в консоль

            return redirect(url_for('index'))

    return render_template('registration.html', title="Регистрация", form=form)


# ____________ END маршруты  для работы с пользователями ____________


if __name__ == '__main__':
    app.run(host='0.0.0.0')
