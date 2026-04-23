from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta

import os

app = Flask(__name__)
app.secret_key = 'vega_secret_key_2024'

# ======================
# МОК-ДАННЫЕ
# ======================

# Пользователи
users = {
    1: {
        'id': 1,
        'name': 'Иван Петров',
        'avatar': 'https://randomuser.me/api/portraits/men/32.jpg',
        'cover': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d',
        'status': 'online',
        'friends_count': 245,
        'subscribers': 89
    },
    2: {
        'id': 2,
        'name': 'Анна Смирнова',
        'avatar': 'https://randomuser.me/api/portraits/women/44.jpg',
        'cover': 'https://images.unsplash.com/photo-1494790108755-2616b612b786',
        'status': 'online',
        'friends_count': 312,
        'subscribers': 156
    },
    3: {
        'id': 3,
        'name': 'Сергей Иванов',
        'avatar': 'https://randomuser.me/api/portraits/men/22.jpg',
        'cover': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb',
        'status': 'online',
        'friends_count': 189,
        'subscribers': 67
    },
    4: {
        'id': 4,
        'name': 'Ольга Кузнецова',
        'avatar': 'https://randomuser.me/api/portraits/women/33.jpg',
        'cover': 'https://images.unsplash.com/photo-1507591064344-4c6ce005-128b',
        'status': 'offline',
        'friends_count': 167,
        'subscribers': 45
    },
    5: {
        'id': 5,
        'name': 'Дмитрий Соколов',
        'avatar': 'https://randomuser.me/api/portraits/men/55.jpg',
        'cover': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d',
        'status': 'online',
        'friends_count': 278,
        'subscribers': 92
    }
}

# Посты
posts = [
    {
        'id': 1,
        'author_id': 2,
        'author': users[2],
        'content': 'Вчера побывала на потрясающей выставке современного искусства! Очень вдохновляет, когда видишь, как творчество может передавать такие глубокие эмоции и идеи. Рекомендую всем, кто будет в городе на этих выходных! 🎨✨',
        'image': 'https://images.unsplash.com/photo-1541961017774-22349e4a1262',
        'likes': 245,
        'comments_count': 42,
        'shares': 5,
        'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
        'privacy': 'public'
    },
    {
        'id': 2,
        'author_id': 3,
        'author': users[3],
        'content': 'Наконец-то завершил большой проект на работе! Полгода упорного труда, и вот результат. Очень благодарен своей команде за поддержку и слаженную работу. 🚀\n\nТеперь можно немного передохнуть и взяться за что-то новое. Кстати, кто что посоветует почитать на тему личной эффективности?',
        'image': None,
        'likes': 189,
        'comments_count': 36,
        'shares': 3,
        'created_at': (datetime.now() - timedelta(hours=5)).isoformat(),
        'privacy': 'friends'
    },
    {
        'id': 3,
        'author_id': 5,
        'author': users[5],
        'content': 'Отличный день для путешествий! 🌄 Решил выбраться за город, чтобы насладиться природой и отдохнуть от городской суеты. Иногда так важно просто остановиться и насладиться моментом.',
        'image': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4',
        'likes': 127,
        'comments_count': 18,
        'shares': 2,
        'created_at': (datetime.now() - timedelta(hours=8)).isoformat(),
        'privacy': 'public'
    }
]

# Истории
stories = [
    {
        'id': 1,
        'author_id': 5,
        'author': users[5],
        'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d',
        'created_at': (datetime.now() - timedelta(hours=3)).isoformat()
    },
    {
        'id': 2,

'author_id': 4,
'author': users[4],
'image': 'https://images.unsplash.com/photo-1494790108755-2616b612b786',
'created_at': (datetime.now() - timedelta(hours=5)).isoformat()
},
{
    'id': 3,
    'author_id': 2,
    'author': users[2],
    'image': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb',
    'created_at': (datetime.now() - timedelta(hours=7)).isoformat()
},
{
    'id': 4,
    'author_id': 3,
    'author': users[3],
    'image': 'https://images.unsplash.com/photo-1507591064344-4c6ce005-128b',
    'created_at': (datetime.now() - timedelta(hours=10)).isoformat()
}
]

# Друзья онлайн
online_friends = [
    users[2],
    users[3],
    users[5]
]

offline_friends = [
    users[4]
]

# Дни рождения
birthdays = [
    {
        'id': 1,
        'name': 'Мария Кузнецова',
        'date': 'Сегодня',
        'avatar': 'https://randomuser.me/api/portraits/women/68.jpg'
    },
    {
        'id': 2,
        'name': 'Дмитрий Соколов',
        'date': 'Завтра',
        'avatar': 'https://randomuser.me/api/portraits/men/55.jpg'
    }
]

# События
events = [
    {
        'id': 1,
        'name': 'Концерт в парке',
        'date': 'Суббота, 15:00',
        'icon': 'music',
        'attendees': 45
    },
    {
        'id': 2,
        'name': 'Встреча выпускников',
        'date': 'Воскресенье, 19:00',
        'icon': 'utensils',
        'attendees': 28
    }
]

# Уведомления
notifications = [
    {'id': 1, 'type': 'friend_request', 'user_id': 4, 'message': 'Ольга Кузнецова хочет добавить вас в друзья',
     'time': '5 мин назад', 'read': False},
    {'id': 2, 'type': 'comment', 'user_id': 2, 'message': 'Анна Смирнова прокомментировала вашу запись',
     'time': '15 мин назад', 'read': False},
    {'id': 3, 'type': 'like', 'user_id': 3, 'message': 'Сергей Иванов оценил вашу фотографию', 'time': '1 час назад',
     'read': True},
    {'id': 4, 'type': 'birthday', 'user_id': 6, 'message': 'У Марии Кузнецовой сегодня день рождения!',
     'time': '2 часа назад', 'read': False},
]


# ======================
# МАРШРУТЫ
# ======================

@app.route('/')
def index():
    """Главная страница - лента новостей"""
    if 'user_id' not in session:
        session['user_id'] = 1  # Автоматическая авторизация для демо

    current_user = users.get(session['user_id'], users[1])

    # Сортируем посты по дате (сначала новые)
    sorted_posts = sorted(posts, key=lambda x: x['created_at'], reverse=True)

    notification_count = sum(1 for n in notifications if not n['read'])

    return render_template('index.html',
                           current_user=current_user,
                           posts=sorted_posts,
                           stories=stories,
                           online_friends=online_friends,
                           offline_friends=offline_friends,
                           birthdays=birthdays,
                           events=events,
                           notifications=notifications,
                           notification_count=notification_count)


@app.route('/create_post', methods=['POST'])
def create_post():
    """Создание нового поста"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401

    data = request.json
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'Текст поста не может быть пустым'}), 400

    new_post = {
        'id': len(posts) + 1,
        'author_id': session['user_id'],
        'author': users[session['user_id']],
        'content': content,
        'image': data.get('image'),
        'likes': 0,
        'comments_count': 0,
        'shares': 0,
        'created_at': datetime.now().isoformat(),
        'privacy': data.get('privacy', 'public')
    }

    posts.insert(0, new_post)

    return jsonify({
        'success': True,
        'message': 'Пост опубликован!',
        'post': new_post
    })

@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    """Лайк поста"""
    for post in posts:
        if post['id'] == post_id:
            post['likes'] += 1
            return jsonify({'success': True, 'likes': post['likes']})

    return jsonify({'error': 'Пост не найден'}), 404


@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    """Добавление комментария"""
    for post in posts:
        if post['id'] == post_id:
            post['comments_count'] += 1
            return jsonify({'success': True, 'comments_count': post['comments_count']})

    return jsonify({'error': 'Пост не найден'}), 404


@app.route('/share_post/<int:post_id>', methods=['POST'])
def share_post(post_id):
    """Репост"""
    for post in posts:
        if post['id'] == post_id:
            post['shares'] += 1
            return jsonify({'success': True, 'shares': post['shares']})

    return jsonify({'error': 'Пост не найден'}), 404


@app.route('/add_story', methods=['POST'])
def add_story():
    """Добавление истории"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401

    data = request.json
    image = data.get('image')

    if not image:
        return jsonify({'error': 'Изображение обязательно'}), 400

    new_story = {
        'id': len(stories) + 1,
        'author_id': session['user_id'],
        'author': users[session['user_id']],
        'image': image,
        'created_at': datetime.now().isoformat()
    }

    stories.insert(0, new_story)

    return jsonify({
        'success': True,
        'message': 'История добавлена!',
        'story': new_story
    })


@app.route('/mark_notifications_read', methods=['POST'])
def mark_notifications_read():
    """Отметить уведомления как прочитанные"""
    for notification in notifications:
        notification['read'] = True

    return jsonify({'success': True})


@app.route('/profile/<int:user_id>')
def profile(user_id):
    """Страница профиля пользователя"""
    if user_id not in users:
        return jsonify({'error': 'Пользователь не найден'}), 404

    user = users[user_id]
    user_posts = [post for post in posts if post['author_id'] == user_id]

    return jsonify({
        'user': user,
        'posts_count': len(user_posts),
        'posts': user_posts[:5]  # Последние 5 постов
    })


@app.route('/friends')
def friends():
    """Страница друзей"""
    return jsonify({
        'online': online_friends,
        'offline': offline_friends,
        'total': len(online_friends) + len(offline_friends)
    })


@app.route('/search')
def search():
    """Поиск"""
    query = request.args.get('q', '').lower()

    if not query:
        return jsonify({'results': []})

    results = []

    # Поиск пользователей
    for user in users.values():
        if query in user['name'].lower():
            results.append({
                'type': 'user',
                'id': user['id'],
                'name': user['name'],
                'avatar': user['avatar'],
                'status': user['status']
            })

    # Поиск постов
    for post in posts:
        if query in post['content'].lower():
            results.append({
                'type': 'post',
                'id': post['id'],
                'author': post['author']['name'],
                'content': post['content'][:100] + '...' if len(post['content']) > 100 else post['content'],
                'created_at': post['created_at']
            })

    return jsonify({'results': results[:10]})  # Ограничиваем 10 результатами


@app.route('/notifications')
def get_notifications():
    """Получить уведомления"""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    if unread_only:
        filtered = [n for n in notifications if not n['read']]
    else:
        filtered = notifications

    return jsonify({
        'notifications': filtered,
        'unread_count': sum(1 for n in notifications if not n['read'])
    })

@app.route("/team")
def team():

    return render_template("team.html")


if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')

    app.run(debug=True, host='0.0.0.0', port=5000)
