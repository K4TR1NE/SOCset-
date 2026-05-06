from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
from functools import wraps
import os
from good import VegaAuth
from events import VegaEvents

app = Flask(__name__)
app.secret_key = 'vega_secret_key_2024'

# Сессия хранится 30 дней
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Инициализация системы авторизации
auth = VegaAuth()

# ======================
# МОК-ДАННЫЕ
# ======================

users = {
    1: {'id': 1, 'name': 'Иван Петров', 'avatar': 'https://randomuser.me/api/portraits/men/32.jpg',
        'cover': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d', 'status': 'online',
        'friends_count': 245, 'subscribers': 89},
    2: {'id': 2, 'name': 'Анна Смирнова', 'avatar': 'https://randomuser.me/api/portraits/women/44.jpg',
        'cover': 'https://images.unsplash.com/photo-1494790108755-2616b612b786', 'status': 'online',
        'friends_count': 312, 'subscribers': 156},
    3: {'id': 3, 'name': 'Сергей Иванов', 'avatar': 'https://randomuser.me/api/portraits/men/22.jpg',
        'cover': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb', 'status': 'online',
        'friends_count': 189, 'subscribers': 67},
    4: {'id': 4, 'name': 'Ольга Кузнецова', 'avatar': 'https://randomuser.me/api/portraits/women/33.jpg',
        'cover': 'https://images.unsplash.com/photo-1507591064344-4c6ce005-128b', 'status': 'offline',
        'friends_count': 167, 'subscribers': 45},
    5: {'id': 5, 'name': 'Дмитрий Соколов', 'avatar': 'https://randomuser.me/api/portraits/men/55.jpg',
        'cover': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d', 'status': 'online',
        'friends_count': 278, 'subscribers': 92}
}

stories = [
    {'id': 1, 'author_id': 5, 'author': users[5],
     'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d',
     'created_at': (datetime.now() - timedelta(hours=3)).isoformat()},
    {'id': 2, 'author_id': 4, 'author': users[4],
     'image': 'https://images.unsplash.com/photo-1494790108755-2616b612b786',
     'created_at': (datetime.now() - timedelta(hours=5)).isoformat()},
    {'id': 3, 'author_id': 2, 'author': users[2],
     'image': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb',
     'created_at': (datetime.now() - timedelta(hours=7)).isoformat()},
    {'id': 4, 'author_id': 3, 'author': users[3],
     'image': 'https://images.unsplash.com/photo-1507591064344-4c6ce005-128b',
     'created_at': (datetime.now() - timedelta(hours=10)).isoformat()}
]

online_friends = [users[2], users[3], users[5]]
offline_friends = [users[4]]

birthdays = [
    {'id': 1, 'name': 'Мария Кузнецова', 'date': 'Сегодня',
     'avatar': 'https://randomuser.me/api/portraits/women/68.jpg'},
    {'id': 2, 'name': 'Дмитрий Соколов', 'date': 'Завтра', 'avatar': 'https://randomuser.me/api/portraits/men/55.jpg'}
]

events = [
    {'id': 1, 'name': 'Концерт в парке', 'date': 'Суббота, 15:00', 'icon': 'music', 'attendees': 45},
    {'id': 2, 'name': 'Встреча выпускников', 'date': 'Воскресенье, 19:00', 'icon': 'utensils', 'attendees': 28}
]

mock_posts = [
    {
        'id': 1, 'author': users[2],
        'content': 'Вчера побывала на потрясающей выставке современного искусства! Очень вдохновляет, когда видишь, как творчество может передавать такие глубокие эмоции и идеи. 🎨✨',
        'image': 'https://images.unsplash.com/photo-1541961017774-22349e4a1262',
        'likes': 245, 'comments_count': 42, 'shares': 5,
        'created_at': (datetime.now() - timedelta(hours=2)).isoformat(), 'privacy': 'public'
    },
    {
        'id': 2, 'author': users[3],
        'content': 'Наконец-то завершил большой проект на работе! Полгода упорного труда, и вот результат. Спасибо команде! 🚀',
        'image': None, 'likes': 189, 'comments_count': 36, 'shares': 3,
        'created_at': (datetime.now() - timedelta(hours=5)).isoformat(), 'privacy': 'friends'
    },
    {
        'id': 3, 'author': users[5],
        'content': 'Отличный день для путешествий! 🌄 Решил выбраться за город, чтобы насладиться природой.',
        'image': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4',
        'likes': 127, 'comments_count': 18, 'shares': 2,
        'created_at': (datetime.now() - timedelta(hours=8)).isoformat(), 'privacy': 'public'
    }
]

communities = [
    {'id': 1, 'name': 'Астрологический клуб', 'description': 'Обсуждаем натальные карты и прогнозы',
     'avatar': 'https://images.unsplash.com/photo-1532968961962-8a0cb3a2d4f5?w=200',
     'cover': 'https://images.unsplash.com/photo-1501139083538-0139583c060f?w=800', 'members_count': 15420,
     'online_count': 342, 'posts_count': 892, 'category': 'Астрология', 'is_verified': True, 'is_subscribed': True},
    {'id': 2, 'name': 'Таро и эзотерика', 'description': 'Расклады Таро и эзотерические практики',
     'avatar': 'https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=200',
     'cover': 'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800', 'members_count': 8930,
     'online_count': 156, 'posts_count': 567, 'category': 'Эзотерика', 'is_verified': True, 'is_subscribed': True},
    {'id': 3, 'name': 'Медитации', 'description': 'Практики медитации и mindfulness',
     'avatar': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=200',
     'cover': 'https://images.unsplash.com/photo-1470137237906-d8a4f71e1962?w=800', 'members_count': 12300,
     'online_count': 234, 'posts_count': 445, 'category': 'Медитация', 'is_verified': False, 'is_subscribed': True},
    {'id': 4, 'name': 'Астрономия', 'description': 'Наблюдения за звездами и космос',
     'avatar': 'https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=200',
     'cover': 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=800', 'members_count': 21500,
     'online_count': 421, 'posts_count': 1234, 'category': 'Наука', 'is_verified': True, 'is_subscribed': False},
    {'id': 5, 'name': 'Гороскопы', 'description': 'Ежедневные гороскопы от астрологов',
     'avatar': 'https://images.unsplash.com/photo-1617483382236-fddc4fc0c2e2?w=200',
     'cover': 'https://images.unsplash.com/photo-1505506874110-6a7a69069a08?w=800', 'members_count': 34200,
     'online_count': 567, 'posts_count': 2156, 'category': 'Гороскопы', 'is_verified': True, 'is_subscribed': True}
]

categories = [
    {'id': 1, 'name': 'Астрология', 'icon': 'fa-star', 'count': 1},
    {'id': 2, 'name': 'Эзотерика', 'icon': 'fa-moon', 'count': 1},
    {'id': 3, 'name': 'Медитация', 'icon': 'fa-om', 'count': 1},
    {'id': 4, 'name': 'Наука', 'icon': 'fa-atom', 'count': 1},
    {'id': 5, 'name': 'Гороскопы', 'icon': 'fa-sun', 'count': 1}
]

friends_list = [
    {'id': 2, 'user': users[2], 'mutual_friends': 45, 'zodiac': '♓ Рыбы', 'last_active': '5 минут назад',
     'is_online': True},
    {'id': 3, 'user': users[3], 'mutual_friends': 32, 'zodiac': '♏ Скорпион', 'last_active': '15 минут назад',
     'is_online': True},
    {'id': 4, 'user': users[4], 'mutual_friends': 28, 'zodiac': '♎ Весы', 'last_active': '2 часа назад',
     'is_online': False},
    {'id': 5, 'user': users[5], 'mutual_friends': 56, 'zodiac': '♉ Телец', 'last_active': '1 минуту назад',
     'is_online': True}
]

friend_requests = [
    {'id': 6, 'name': 'Мария Кузнецова', 'avatar': 'https://randomuser.me/api/portraits/women/68.jpg',
     'mutual_friends': 12, 'zodiac': '♊ Близнецы'},
    {'id': 7, 'name': 'Александр Волков', 'avatar': 'https://randomuser.me/api/portraits/men/45.jpg',
     'mutual_friends': 8, 'zodiac': '♌ Лев'}
]

notifications = [
    {'id': 1, 'type': 'friend_request', 'message': 'Ольга Кузнецова хочет добавить вас в друзья', 'time': '5 мин назад',
     'read': False},
    {'id': 2, 'type': 'comment', 'message': 'Анна Смирнова прокомментировала вашу запись', 'time': '15 мин назад',
     'read': False},
    {'id': 3, 'type': 'like', 'message': 'Сергей Иванов оценил вашу фотографию', 'time': '1 час назад', 'read': True},
    {'id': 4, 'type': 'birthday', 'message': 'У Марии Кузнецовой сегодня день рождения!', 'time': '2 часа назад',
     'read': False}
]


# ======================
# ДЕКОРАТОР ДЛЯ ПРОВЕРКИ АВТОРИЗАЦИИ
# ======================

def login_required(f):
    """Декоратор для защиты маршрутов"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'info')
            return redirect(url_for('login'))

        user = auth.get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            flash('Сессия истекла. Войдите снова.', 'error')
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


# ======================
# ФИЛЬТР ДЛЯ ЧИСЕЛ
# ======================

@app.template_filter('format_number')
def format_number(value):
    """Форматирование чисел: 15420 -> 15.4K"""
    try:
        value = int(value)
        if value >= 1000000:
            return f"{value / 1000000:.1f}M"
        elif value >= 1000:
            return f"{value / 1000:.1f}K"
        return str(value)
    except:
        return str(value)


# ======================
# ГЛАВНАЯ СТРАНИЦА (ЛЕНТА НОВОСТЕЙ)
# ======================

@app.route('/')
@login_required
def index():
    """Главная страница - лента новостей"""
    session.permanent = True

    user = auth.get_user_by_id(session['user_id'])

    # Получаем посты из БД
    posts_from_db = auth.get_posts()

    # Если постов из БД меньше 3, добавляем мок-посты
    if len(posts_from_db) < 3:
        posts_list = posts_from_db + mock_posts[:3 - len(posts_from_db)]
    else:
        posts_list = posts_from_db

    notification_count = sum(1 for n in notifications if not n['read'])

    return render_template('index.html',
                           current_user=user,
                           posts=posts_list,
                           stories=stories,
                           online_friends=online_friends,
                           offline_friends=offline_friends,
                           birthdays=birthdays,
                           events=events,
                           notification_count=notification_count)


# ======================
# АВТОРИЗАЦИЯ
# ======================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    # Если уже вошли - на главную
    if 'user_id' in session:
        user = auth.get_user_by_id(session['user_id'])
        if user:
            return redirect(url_for('index'))
        session.clear()

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember')

        if not email or not password:
            flash('Заполните все поля', 'error')
            return render_template('login.html')

        success, message, user = auth.login(
            email=email,
            password=password,
            ip_address=request.remote_addr
        )

        if success and user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']

            if remember:
                session.permanent = True

            flash(message, 'success')
            return redirect(url_for('index'))
        else:
            flash(message, 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    # Если уже вошли - на главную
    if 'user_id' in session:
        user = auth.get_user_by_id(session['user_id'])
        if user:
            return redirect(url_for('index'))
        session.clear()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()
        zodiac = request.form.get('zodiac', 'Лев')

        if not name or not email or not password:
            flash('Заполните все обязательные поля', 'error')
            return render_template('register.html')

        success, message, user = auth.register(
            name=name,
            email=email,
            password=password,
            password_confirm=password_confirm,
            zodiac=zodiac
        )

        if success and user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session.permanent = True

            flash(message, 'success')
            return redirect(url_for('index'))
        else:
            flash(message, 'error')

    return render_template('register.html')


@app.route('/logout')
def logout():
    """Выход из системы"""
    if 'user_id' in session:
        try:
            auth.logout(session['user_id'])
        except:
            pass

    session.clear()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('login'))


# ======================
# ОСНОВНЫЕ СТРАНИЦЫ
# ======================

@app.route('/profile')
@login_required
def profile_page():
    """Страница профиля"""
    user = auth.get_user_by_id(session['user_id'])
    stats = auth.get_user_stats(session['user_id'])

    # Получаем посты пользователя
    user_posts = auth.get_user_posts(session['user_id'])

    # Если нет своих постов, показываем мок-посты
    if not user_posts:
        user_posts = mock_posts[:2]

    # Гороскоп
    zodiac = user.get('zodiac', 'Лев')
    horoscope = {
        'name': zodiac,
        'emoji': '♌',
        'element': 'Огонь',
        'planet': 'Солнце',
        'date_range': '23 июля - 22 августа',
        'description': f'{zodiac} - уникальный знак зодиака.',
        'today_horoscope': 'Сегодня звезды благоволят вашему знаку! Отличный день для новых начинаний.',
        'love_horoscope': 'В личной жизни наступает гармоничный период.',
        'career_horoscope': 'На работе вас ждет признание.',
        'lucky_numbers': [1, 8, 15, 23, 42],
        'lucky_color': 'Золотой',
        'compatibility': ['Овен', 'Стрелец', 'Близнецы']
    }

    cities = ['Москва', 'Санкт-Петербург', 'Ижевск', 'Казань', 'Екатеринбург']

    return render_template('profile.html',
                           current_user=user,
                           user=user,
                           posts=user_posts,
                           horoscope=horoscope,
                           stats=stats,
                           cities=cities,
                           notification_count=0)


@app.route('/friends')
@login_required
def friends_page():
    """Страница друзей"""
    user = auth.get_user_by_id(session['user_id'])
    return render_template('friends.html',
                           current_user=user,
                           friends=friends_list,
                           friend_requests=friend_requests,
                           notification_count=0)


@app.route('/communities')
@login_required
def communities_page():
    """Страница сообществ"""
    user = auth.get_user_by_id(session['user_id'])
    return render_template('communities.html',
                           current_user=user,
                           communities=communities,
                           categories=categories,
                           notification_count=0)


@app.route('/settings')
@login_required
def settings_page():
    """Страница настроек"""
    user = auth.get_user_by_id(session['user_id'])
    return render_template('settings.html',
                           current_user=user,
                           notification_count=0)


# ======================
# API МАРШРУТЫ
# ======================

@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    """Создание нового поста"""
    try:
        data = request.get_json() or {}
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'success': False, 'error': 'Текст не может быть пустым'}), 400

        post_id = auth.create_post(
            session['user_id'],
            content,
            data.get('image'),
            data.get('privacy', 'public')
        )

        if post_id:
            return jsonify({
                'success': True,
                'message': 'Пост опубликован!',
                'post_id': post_id
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка при создании поста'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    """Лайк поста"""
    try:
        success, message = auth.like_post(session['user_id'], post_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    """Добавление комментария"""
    try:
        data = request.get_json() or {}
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'success': False, 'error': 'Комментарий не может быть пустым'}), 400

        success, message = auth.add_comment(session['user_id'], post_id, content)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/share_post/<int:post_id>', methods=['POST'])
@login_required
def share_post(post_id):
    """Поделиться постом"""
    try:
        conn = auth.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE posts SET shares = shares + 1 WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Пост опубликован!'})
    except:
        return jsonify({'success': True, 'message': 'Пост опубликован!'})


@app.route('/notifications')
@login_required
def get_notifications():
    """Получить уведомления"""
    return jsonify({'notifications': notifications, 'unread_count': sum(1 for n in notifications if not n['read'])})


@app.route('/mark_notifications_read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Отметить уведомления как прочитанные"""
    for n in notifications:
        n['read'] = True
    return jsonify({'success': True})

events_manager = VegaEvents()

@app.route('/events')
@login_required
def events_page():
    user = auth.get_user_by_id(session['user_id'])

    # Параметры
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    selected_date = request.args.get('date', '')
    selected_day = int(selected_date.split('-')[2]) if selected_date else None

    # Календарь
    calendar = events_manager.get_calendar_data(year, month, session['user_id'])

    # События на выбранный день
    day_events = []
    if selected_date:
        day_events = events_manager.get_events_by_date(selected_date, session['user_id'])

    # Ближайшие события
    upcoming = events_manager.get_upcoming_events(session['user_id'])

    # Предыдущий/следующий месяц
    if month == 1:
        prev_month = (year - 1, 12)
    else:
        prev_month = (year, month - 1)

    if month == 12:
        next_month = (year + 1, 1)
    else:
        next_month = (year, month + 1)

    return render_template('events.html',
                           current_user=user,
                           calendar=calendar,
                           day_events=day_events,
                           upcoming_events=upcoming,
                           selected_date=selected_date,
                           selected_day=selected_day,
                           prev_month=prev_month,
                           next_month=next_month,
                           notification_count=0)


@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    title = request.form.get('title', '').strip()
    event_date = request.form.get('event_date', '').strip()
    description = request.form.get('description', '').strip()
    color = request.form.get('color', '#9d7be8')
    icon = request.form.get('icon', 'fa-calendar')

    if not title or not event_date:
        flash('Название и дата обязательны', 'error')
        return redirect(url_for('events_page'))

    success, message, _ = events_manager.add_event(
        session['user_id'], title, event_date, description, color, icon
    )

    if success:
        flash('Событие добавлено!', 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('events_page', date=event_date))


@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    success, message = events_manager.delete_event(event_id, session['user_id'])
    return jsonify({'success': success, 'message': message})


# ======================
# ОБРАБОТКА ОШИБОК
# ======================

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('index'))


@app.errorhandler(500)
def server_error(e):
    return render_template('login.html'), 500


# ======================
# ЗАПУСК
# ======================

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')

    print("\n" + "=" * 50)
    print("  VEGA - Астрологическая социальная сеть")
    print("=" * 50)
    print(f"  Сервер: http://127.0.0.1:5000")
    print(f"  Вход: http://127.0.0.1:5000/login")
    print(f"  Регистрация: http://127.0.0.1:5000/register")
    print("=" * 50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)