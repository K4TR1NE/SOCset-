from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)
app.secret_key = 'vega_secret_key_2024'

@app.template_filter('format_number')
def format_number(value):
    """Форматирование чисел: 15420 -> 15.4K"""
    if value >= 10000:
        return f"{value/1000:.1f}K"
    elif value >= 1000:
        return f"{value/1000:.1f}K"
    return str(value)

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

# Сообщества
communities = [
    {
        'id': 1,
        'name': 'Астрологический клуб',
        'description': 'Обсуждаем натальные карты, транзиты и астрологические прогнозы',
        'avatar': 'https://images.unsplash.com/photo-1532968961962-8a0cb3a2d4f5?w=200',
        'cover': 'https://images.unsplash.com/photo-1501139083538-0139583c060f?w=800',
        'members_count': 15420,
        'online_count': 342,
        'posts_count': 892,
        'category': 'Астрология',
        'is_verified': True,
        'is_subscribed': True
    },
    {
        'id': 2,
        'name': 'Таро и эзотерика',
        'description': 'Расклады Таро, руны, хиромантия и другие эзотерические практики',
        'avatar': 'https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=200',
        'cover': 'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800',
        'members_count': 8930,
        'online_count': 156,
        'posts_count': 567,
        'category': 'Эзотерика',
        'is_verified': True,
        'is_subscribed': True
    },
    {
        'id': 3,
        'name': 'Медитации и осознанность',
        'description': 'Практики медитации, mindfulness и духовного развития',
        'avatar': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=200',
        'cover': 'https://images.unsplash.com/photo-1470137237906-d8a4f71e1962?w=800',
        'members_count': 12300,
        'online_count': 234,
        'posts_count': 445,
        'category': 'Медитация',
        'is_verified': False,
        'is_subscribed': True
    },
    {
        'id': 4,
        'name': 'Астрономия для всех',
        'description': 'Наблюдения за звездами, телескопы, космические явления',
        'avatar': 'https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=200',
        'cover': 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=800',
        'members_count': 21500,
        'online_count': 421,
        'posts_count': 1234,
        'category': 'Наука',
        'is_verified': True,
        'is_subscribed': False
    },
    {
        'id': 5,
        'name': 'Кристаллы и минералы',
        'description': 'Мир драгоценных камней, их свойства и влияние на человека',
        'avatar': 'https://images.unsplash.com/photo-1599904869085-1c0bcc114423?w=200',
        'cover': 'https://images.unsplash.com/photo-1515344905723-babc01aac23d?w=800',
        'members_count': 7650,
        'online_count': 98,
        'posts_count': 321,
        'category': 'Кристаллы',
        'is_verified': False,
        'is_subscribed': False
    },
    {
        'id': 6,
        'name': 'Гороскопы и прогнозы',
        'description': 'Ежедневные, недельные и месячные гороскопы от профессиональных астрологов',
        'avatar': 'https://images.unsplash.com/photo-1617483382236-fddc4fc0c2e2?w=200',
        'cover': 'https://images.unsplash.com/photo-1505506874110-6a7a69069a08?w=800',
        'members_count': 34200,
        'online_count': 567,
        'posts_count': 2156,
        'category': 'Гороскопы',
        'is_verified': True,
        'is_subscribed': True
    },
    {
        'id': 7,
        'name': 'Йога и здоровье',
        'description': 'Практика йоги, здоровый образ жизни и аюрведа',
        'avatar': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=200',
        'cover': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800',
        'members_count': 18900,
        'online_count': 312,
        'posts_count': 987,
        'category': 'Здоровье',
        'is_verified': True,
        'is_subscribed': False
    },
    {
        'id': 8,
        'name': 'Нумерология',
        'description': 'Расчеты чисел судьбы, квадрат Пифагора и числовые коды',
        'avatar': 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=200',
        'cover': 'https://images.unsplash.com/photo-1509228627152-72ae9ae6848d?w=800',
        'members_count': 5430,
        'online_count': 67,
        'posts_count': 234,
        'category': 'Нумерология',
        'is_verified': False,
        'is_subscribed': False
    }
]

# Категории сообществ
categories = [
    {'id': 1, 'name': 'Астрология', 'icon': 'fa-star', 'count': 3},
    {'id': 2, 'name': 'Эзотерика', 'icon': 'fa-moon', 'count': 1},
    {'id': 3, 'name': 'Медитация', 'icon': 'fa-om', 'count': 1},
    {'id': 4, 'name': 'Наука', 'icon': 'fa-atom', 'count': 1},
    {'id': 5, 'name': 'Гороскопы', 'icon': 'fa-sun', 'count': 1},
    {'id': 6, 'name': 'Здоровье', 'icon': 'fa-heart', 'count': 1}
]

# Друзья с дополнительной информацией
friends_list = [
    {
        'id': 2,
        'user': users[2],
        'mutual_friends': 45,
        'zodiac': '♓ Рыбы',
        'last_active': '5 минут назад',
        'is_online': True
    },
    {
        'id': 3,
        'user': users[3],
        'mutual_friends': 32,
        'zodiac': '♏ Скорпион',
        'last_active': '15 минут назад',
        'is_online': True
    },
    {
        'id': 4,
        'user': users[4],
        'mutual_friends': 28,
        'zodiac': '♎ Весы',
        'last_active': '2 часа назад',
        'is_online': False
    },
    {
        'id': 5,
        'user': users[5],
        'mutual_friends': 56,
        'zodiac': '♉ Телец',
        'last_active': '1 минуту назад',
        'is_online': True
    }
]

# Заявки в друзья
friend_requests = [
    {
        'id': 6,
        'name': 'Мария Кузнецова',
        'avatar': 'https://randomuser.me/api/portraits/women/68.jpg',
        'mutual_friends': 12,
        'zodiac': '♊ Близнецы'
    },
    {
        'id': 7,
        'name': 'Александр Волков',
        'avatar': 'https://randomuser.me/api/portraits/men/45.jpg',
        'mutual_friends': 8,
        'zodiac': '♌ Лев'
    }
]

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


@app.route('/friends')
def friends_page():
    """Страница друзей"""
    if 'user_id' not in session:
        session['user_id'] = 1

    current_user = users.get(session['user_id'], users[1])
    notification_count = sum(1 for n in notifications if not n['read'])

    return render_template('friends.html',
                           current_user=current_user,
                           friends=friends_list,
                           friend_requests=friend_requests,
                           notification_count=notification_count)


@app.route('/communities')
def communities_page():
    """Страница сообществ"""
    if 'user_id' not in session:
        session['user_id'] = 1

    current_user = users.get(session['user_id'], users[1])
    notification_count = sum(1 for n in notifications if not n['read'])

    return render_template('communities.html',
                           current_user=current_user,
                           communities=communities,
                           categories=categories,
                           notification_count=notification_count)


@app.route('/settings')
def settings_page():
    """Страница настроек"""
    if 'user_id' not in session:
        session['user_id'] = 1

    current_user = users.get(session['user_id'], users[1])
    notification_count = sum(1 for n in notifications if not n['read'])

    return render_template('settings.html',
                           current_user=current_user,
                           notification_count=notification_count)


@app.route('/api/friends')
def get_friends():
    """API для получения списка друзей"""
    return jsonify({
        'friends': friends_list,
        'online_count': sum(1 for f in friends_list if f['is_online']),
        'total_count': len(friends_list)
    })


@app.route('/api/communities')
def get_communities():
    """API для получения списка сообществ"""
    category = request.args.get('category', '')
    subscribed_only = request.args.get('subscribed_only', 'false').lower() == 'true'

    filtered = communities

    if category:
        filtered = [c for c in filtered if c['category'] == category]

    if subscribed_only:
        filtered = [c for c in filtered if c['is_subscribed']]

    return jsonify({
        'communities': filtered,
        'total_count': len(filtered)
    })


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

    # Поиск сообществ
    for community in communities:
        if query in community['name'].lower() or query in community['description'].lower():
            results.append({
                'type': 'community',
                'id': community['id'],
                'name': community['name'],
                'members_count': community['members_count'],
                'avatar': community['avatar']
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


if __name__ == '__main__':
    # Создаем папку templates, если её нет
    if not os.path.exists('templates'):
        os.makedirs('templates')

    app.run(debug=True, host='0.0.0.0', port=5000)