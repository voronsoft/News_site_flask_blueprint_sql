import config_app
from models import db, Post

from flask import Flask, jsonify

# создаем приложение
api = Flask(__name__)
# загружаем настройки для приложения из файла настроек
api.config.from_object(config_app)
#  выполняет инициализацию объекта SQLAlchemy для Flask-приложения
db.init_app(api)


# api для получения всего перечня новостей на сайте
@api.route('/api/show-all-news', methods=['GET'])
def get_all_news():
    # Получаем список новостей из базы данных
    list_posts = Post.query.all()

    # Создаем список словарей для представления новостей в формате JSON
    news_data = []
    for post in list_posts:
        news_data.append({
            "id": post.id,
            "autor": post.autor,
            "title": post.title,
            "short_story": post.short_story,
            "full_story": post.full_story,
            "alt_name": post.alt_name,
        })

    # Преобразуем список новостей в JSON и вернем его
    return jsonify(news_data)


# api для получения данных о конкретной новости с сайта
@api.route('/api/show-news/<int:post_id>', methods=['GET'])
def get_news(post_id):
    # Получаем список новостей из базы данных
    post = Post.query.get(post_id)

    # Создаем список словарей для представления новостей в формате JSON
    post_data = {
        "id": post.id,
        "autor": post.autor,
        "title": post.title,
        "short_story": post.short_story,
        "full_story": post.full_story,
        "alt_name": post.alt_name,
    }
    # Преобразуем список новостей в JSON и вернем его
    return jsonify(post_data)


if __name__ == '__main__':
    api.run(host='0.0.0.0')
