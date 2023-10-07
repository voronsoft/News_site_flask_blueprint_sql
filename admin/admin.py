from flask import Blueprint, render_template, session, request
from models import Users, Post

admin = Blueprint('admin', __name__, template_folder="templates", static_folder="static")


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
    users = Users.query.all()  # Извлекаем всех пользователей из базы данных

    return render_template('admin/admin_users.html', title="Пользователи сайта", users=users)


# маршрут перечня новостей в админ панели
@admin.route('/show-posts')
def show_posts():
    posts = Post.query.all()  # Извлекаем все новости с сайта

    return render_template('admin/admin_show_posts.html', title="Список новостей для редактирования", posts=posts)


# маршрут для редактирования новости
@admin.route('/edit-post/<int:post_id>', methods=['POST', 'GET'])
def edit_post(post_id):
    post_data_edit = Post.query.filter_by(id=post_id).first()
    if request.method == 'GET':
        return render_template('edit_post.html', title='Редактирование новости', post_data_edit=post_data_edit)
    if request.method == "POST":
        # TODO реализовать метод записи в базу данных
        print("Данные изменены - заглушка")
        print(request.form)  # просмотр в консоли
        # Перенаправление на другую страницу (на маршрут редактируемой страницы)
        return redirect(url_for('full_post', post_id=post_id))
