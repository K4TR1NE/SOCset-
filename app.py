from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
from functools import wraps
import os
import random
import sqlite3
import secrets
from werkzeug.utils import secure_filename
from auth import VegaAuth
from profile import VegaProfile
from events import VegaEvents

app = Flask(__name__)
app.secret_key = 'vega_secret_key_2024_CHANGE_THIS_IN_PRODUCTION'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.jinja_env.globals.update(zip=zip)

# Настройки загрузки файлов
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'avi', 'mov'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB


# CSRF защита
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']


app.jinja_env.globals['csrf_token'] = generate_csrf_token


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Инициализация
auth = VegaAuth()
profile_manager = VegaProfile()
events_manager = VegaEvents()


# Таблица галереи
def init_gallery_table():
    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT DEFAULT 'image',
            caption TEXT DEFAULT '',
            post_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()


init_gallery_table()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Войдите в систему', 'info')
            return redirect(url_for('login'))
        user = auth.get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


def generate_random_horoscope(zodiac):
    info = {
        'Овен': {'emoji': '♈', 'element': 'Огонь', 'planet': 'Марс', 'date_range': '21.03 - 19.04'},
        'Телец': {'emoji': '♉', 'element': 'Земля', 'planet': 'Венера', 'date_range': '20.04 - 20.05'},
        'Близнецы': {'emoji': '♊', 'element': 'Воздух', 'planet': 'Меркурий', 'date_range': '21.05 - 20.06'},
        'Рак': {'emoji': '♋', 'element': 'Вода', 'planet': 'Луна', 'date_range': '21.06 - 22.07'},
        'Лев': {'emoji': '♌', 'element': 'Огонь', 'planet': 'Солнце', 'date_range': '23.07 - 22.08'},
        'Дева': {'emoji': '♍', 'element': 'Земля', 'planet': 'Меркурий', 'date_range': '23.08 - 22.09'},
        'Весы': {'emoji': '♎', 'element': 'Воздух', 'planet': 'Венера', 'date_range': '23.09 - 22.10'},
        'Скорпион': {'emoji': '♏', 'element': 'Вода', 'planet': 'Плутон', 'date_range': '23.10 - 21.11'},
        'Стрелец': {'emoji': '♐', 'element': 'Огонь', 'planet': 'Юпитер', 'date_range': '22.11 - 21.12'},
        'Козерог': {'emoji': '♑', 'element': 'Земля', 'planet': 'Сатурн', 'date_range': '22.12 - 19.01'},
        'Водолей': {'emoji': '♒', 'element': 'Воздух', 'planet': 'Уран', 'date_range': '20.01 - 18.02'},
        'Рыбы': {'emoji': '♓', 'element': 'Вода', 'planet': 'Нептун', 'date_range': '19.02 - 20.03'}
    }.get(zodiac, {'emoji': '♌', 'element': 'Огонь', 'planet': 'Солнце', 'date_range': '23.07 - 22.08'})

    return {
        'name': zodiac, 'emoji': info['emoji'], 'element': info['element'],
        'planet': info['planet'], 'date_range': info['date_range'],
        'today': random.choice(["Звезды благоволят!", "Отличный день!", "Прислушайтесь к интуиции."]),
        'love': random.choice(["Гармония в отношениях.", "Возможно новое знакомство."]),
        'career': random.choice(["Успех в делах!", "Хороший день для переговоров."]),
        'advice': random.choice(["Носите счастливый цвет.", "Будьте открыты новому."]),
        'lucky_number': random.randint(1, 99),
        'lucky_color': random.choice(['Золотой', 'Фиолетовый', 'Синий', 'Зеленый']),
        'lucky_color_code': random.choice(['#ffd700', '#9d7be8', '#4a90d9', '#4ecdc4']),
        'energy': random.randint(60, 100)
    }


# ====================== МАРШРУТЫ ======================

@app.route('/')
@login_required
def index():
    session.permanent = True
    user = auth.get_user_by_id(session['user_id'])
    posts_list = auth.get_posts()

    # Получаем файлы из галереи для каждого поста
    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gallery ORDER BY created_at DESC')
    all_gallery_items = [dict(item) for item in cursor.fetchall()]
    conn.close()

    # Группируем файлы по post_id
    for post in posts_list:
        post['files'] = [item['file_path'] for item in all_gallery_items if item.get('post_id') == post['id']]
        # Устанавливаем author_id для проверки в шаблоне
        if 'author_id' not in post:
            post['author_id'] = post.get('author_id', post.get('author', {}).get('id'))

    real_friends = auth.get_friends(session['user_id'])
    online_friends = [f for f in real_friends if f.get('status') == 'online']
    offline_friends = [f for f in real_friends if f.get('status') != 'online']

    upcoming_events = events_manager.get_upcoming_events(session['user_id'], 5)
    formatted_events = [{
        'name': e.get('title', e.get('name', 'Событие')),
        'date': e.get('event_date', e.get('date', '')),
        'icon': e.get('icon', 'star'),
        'color': e.get('color', '#9d7be8')
    } for e in upcoming_events[:5]]

    return render_template('index.html', current_user=user, posts=posts_list, all_items=all_gallery_items,
                           online_friends=online_friends, offline_friends=offline_friends,
                           events=formatted_events, notification_count=0)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if auth.get_user_by_id(session['user_id']):
            return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not email or not password:
            flash('Заполните все поля', 'error')
        else:
            success, message, user = auth.login(email, password, request.remote_addr)
            if success and user:
                session['user_id'] = user['id']
                session.permanent = True
                # Генерируем CSRF токен при входе
                session['csrf_token'] = secrets.token_hex(16)
                flash(message, 'success')
                return redirect(url_for('index'))
            flash(message, 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        if auth.get_user_by_id(session['user_id']):
            return redirect(url_for('index'))
    if request.method == 'POST':
        success, message, user = auth.register(
            request.form.get('name', '').strip(),
            request.form.get('email', '').strip(),
            request.form.get('password', '').strip(),
            request.form.get('password_confirm', '').strip(),
            request.form.get('zodiac', 'Лев')
        )
        if success and user:
            session['user_id'] = user['id']
            session.permanent = True
            session['csrf_token'] = secrets.token_hex(16)
            flash(message, 'success')
            return redirect(url_for('index'))
        flash(message, 'error')
    return render_template('register.html')


@app.route('/logout')
def logout():
    if 'user_id' in session:
        auth.logout(session['user_id'])
    session.clear()
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile_page():
    user = auth.get_user_by_id(session['user_id'])
    stats = profile_manager.get_user_stats(session['user_id'])
    user_posts = auth.get_user_posts(session['user_id'])

    # Получаем все файлы из галереи
    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gallery ORDER BY created_at DESC')
    all_gallery_items = [dict(item) for item in cursor.fetchall()]
    conn.close()

    horoscope = generate_random_horoscope(user.get('zodiac', 'Лев'))
    return render_template('profile.html', current_user=user, user=user,
                           posts=user_posts, horoscope=horoscope, stats=stats,
                           notification_count=0, all_items=all_gallery_items)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # CSRF проверка
    if request.form.get('csrf_token') != session.get('csrf_token'):
        flash('Ошибка безопасности. Попробуйте снова.', 'error')
        return redirect(url_for('profile_page'))

    data = {k: request.form.get(k, '').strip() for k in ['name', 'bio', 'city', 'phone', 'birthday', 'zodiac']}

    # Добавляем валидацию
    if data.get('phone') and len(data['phone']) > 20:
        flash('Номер телефона слишком длинный', 'error')
        return redirect(url_for('profile_page'))

    if data.get('birthday'):
        try:
            datetime.strptime(data['birthday'], '%Y-%m-%d')
        except ValueError:
            flash('Неверный формат даты рождения', 'error')
            return redirect(url_for('profile_page'))

    success, message = profile_manager.update_profile(session['user_id'], data)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('profile_page'))


@app.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    if request.form.get('csrf_token') != session.get('csrf_token'):
        flash('Ошибка безопасности', 'error')
        return redirect(url_for('profile_page'))

    url = request.form.get('avatar_url', '').strip()
    if url:
        if url.startswith(('http://', 'https://')):
            success, message = profile_manager.update_avatar(session['user_id'], url)
            flash(message, 'success' if success else 'error')
        else:
            flash('Некорректный URL', 'error')
    return redirect(url_for('profile_page'))


@app.route('/friends')
@login_required
def friends_page():
    user = auth.get_user_by_id(session['user_id'])
    friends = auth.get_friends(session['user_id'])
    incoming = auth.get_friend_requests(session['user_id'])
    all_users = auth.get_all_users(session['user_id'])
    for u in all_users:
        u['friend_status'] = auth.get_friend_status(session['user_id'], u['id'])
    return render_template('friends.html', current_user=user, friends=friends,
                           incoming_requests=incoming, all_users=all_users, notification_count=0)


@app.route('/send_friend_request/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    s, m = auth.send_friend_request(session['user_id'], user_id)
    return jsonify({'success': s, 'message': m})


@app.route('/accept_friend_request/<int:request_id>', methods=['POST'])
@login_required
def accept_friend_request(request_id):
    s, m = auth.accept_friend_request(request_id, session['user_id'])
    return jsonify({'success': s, 'message': m})


@app.route('/decline_friend_request/<int:request_id>', methods=['POST'])
@login_required
def decline_friend_request(request_id):
    s, m = auth.decline_friend_request(request_id, session['user_id'])
    return jsonify({'success': s, 'message': m})


@app.route('/remove_friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    s, m = auth.remove_friend(session['user_id'], friend_id)
    return jsonify({'success': s, 'message': m})


@app.route('/communities')
@login_required
def communities_page():
    user = auth.get_user_by_id(session['user_id'])
    # Убираем фильтр |format_number - просто передаем числа как есть
    communities = [
        {'id': 1, 'name': 'Астрологический клуб', 'description': 'Натальные карты и прогнозы',
         'avatar': 'https://images.unsplash.com/photo-1532968961962-8a0cb3a2d4f5?w=200', 'members_count': 15420,
         'online_count': 342, 'posts_count': 892, 'category': 'Астрология', 'is_verified': True, 'is_subscribed': True},
        {'id': 2, 'name': 'Таро и эзотерика', 'description': 'Расклады Таро и практики',
         'avatar': 'https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=200', 'members_count': 8930,
         'online_count': 156, 'posts_count': 567, 'category': 'Эзотерика', 'is_verified': True, 'is_subscribed': True},
        {'id': 3, 'name': 'Гороскопы', 'description': 'Ежедневные гороскопы',
         'avatar': 'https://images.unsplash.com/photo-1617483382236-fddc4fc0c2e2?w=200', 'members_count': 34200,
         'online_count': 567, 'posts_count': 2156, 'category': 'Гороскопы', 'is_verified': True, 'is_subscribed': True}
    ]
    categories = [
        {'id': 1, 'name': 'Астрология', 'icon': 'fa-star', 'count': 1},
        {'id': 2, 'name': 'Эзотерика', 'icon': 'fa-moon', 'count': 1},
        {'id': 3, 'name': 'Гороскопы', 'icon': 'fa-sun', 'count': 1}
    ]
    return render_template('communities.html', current_user=user, communities=communities,
                           categories=categories, notification_count=0)


@app.route('/gallery')
@login_required
def gallery_page():
    user = auth.get_user_by_id(session['user_id'])
    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gallery WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    items = [dict(i) for i in cursor.fetchall()]
    conn.close()
    photos = [i for i in items if i['file_type'] == 'image']
    videos = [i for i in items if i['file_type'] == 'video']
    return render_template('gallery.html', current_user=user, photos=photos, videos=videos,
                           all_items=items, notification_count=0)


@app.route('/chat')
@login_required
def chat_page():
    user = auth.get_user_by_id(session['user_id'])
    return render_template('chat.html', current_user=user, notification_count=0)


@app.route('/events')
@login_required
def events_page():
    user = auth.get_user_by_id(session['user_id'])
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    selected_date = request.args.get('date', '')
    selected_day = int(selected_date.split('-')[2]) if selected_date else None
    calendar = events_manager.get_calendar_data(year, month, session['user_id'])
    day_events = events_manager.get_events_by_date(selected_date, session['user_id']) if selected_date else []
    prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    return render_template('events.html', current_user=user, calendar=calendar,
                           day_events=day_events, selected_date=selected_date,
                           selected_day=selected_day, prev_month=prev_month,
                           next_month=next_month, notification_count=0)


@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    if request.form.get('csrf_token') != session.get('csrf_token'):
        flash('Ошибка безопасности', 'error')
        return redirect(url_for('events_page'))

    title = request.form.get('title', '').strip()
    event_date = request.form.get('event_date', '').strip()
    if not title or not event_date:
        flash('Название и дата обязательны', 'error')
        return redirect(url_for('events_page'))
    s, m, _ = events_manager.add_event(session['user_id'], title, event_date,
                                       request.form.get('description', '').strip(),
                                       request.form.get('color', '#9d7be8'),
                                       request.form.get('icon', 'fa-calendar'))
    flash(m, 'success' if s else 'error')
    return redirect(url_for('events_page', date=event_date))


@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    s, m = events_manager.delete_event(event_id, session['user_id'])
    return jsonify({'success': s, 'message': m})


@app.route('/settings')
@login_required
def settings_page():
    user = auth.get_user_by_id(session['user_id'])
    return render_template('settings.html', current_user=user, notification_count=0)


@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    """Создание поста с загрузкой фото/видео"""
    content = request.form.get('content', '').strip()
    files = request.files.getlist('media')
    uploaded = []

    if not content and not files:
        return jsonify({'success': False, 'error': 'Напишите текст или прикрепите файл'}), 400

    post_id = auth.create_post(session['user_id'], content if content else '')

    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()

    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(
                f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            ext = filename.rsplit('.', 1)[1].lower()
            file_type = 'video' if ext in ['mp4', 'webm', 'avi', 'mov'] else 'image'

            cursor.execute(
                'INSERT INTO gallery (user_id, file_path, file_type, caption, post_id) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'], f'/static/uploads/{filename}', file_type, content, post_id)
            )
            uploaded.append({'path': f'/static/uploads/{filename}', 'type': file_type})

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Пост опубликован!',
        'post_id': post_id,
        'files': [f['path'] for f in uploaded]
    })


@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    success, message, new_count, action = auth.like_post(session['user_id'], post_id)
    return jsonify({
        'success': success,
        'message': message,
        'new_count': new_count,
        'action': action
    })

@app.route('/get_comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    """Получить все комментарии к посту"""
    comments = auth.get_comments(post_id)
    return jsonify({'success': True, 'comments': comments})

@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False}), 400
    s, m = auth.add_comment(session['user_id'], post_id, content)
    return jsonify({'success': s, 'message': m})


@app.route('/share_post/<int:post_id>', methods=['POST'])
@login_required
def share_post(post_id):
    return jsonify({'success': True, 'message': 'Репост сделан!'})


# ========== НОВЫЕ МАРШРУТЫ ДЛЯ РЕДАКТИРОВАНИЯ/УДАЛЕНИЯ ПОСТОВ ==========

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Удаление поста и связанных с ним файлов"""
    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()

    # Проверяем, что пост принадлежит пользователю
    cursor.execute('SELECT id, image FROM posts WHERE id = ? AND author_id = ?', (post_id, session['user_id']))
    post = cursor.fetchone()

    if not post:
        conn.close()
        return jsonify({'success': False, 'message': 'Пост не найден'}), 404

    # Удаляем связанные файлы из галереи
    cursor.execute('SELECT file_path FROM gallery WHERE post_id = ?', (post_id,))
    files = cursor.fetchall()
    for file in files:
        file_path = file[0].lstrip('/')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

    # Удаляем записи из галереи
    cursor.execute('DELETE FROM gallery WHERE post_id = ?', (post_id,))

    # Удаляем лайки и комментарии (каскадно)
    cursor.execute('DELETE FROM likes WHERE post_id = ?', (post_id,))
    cursor.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))

    # Удаляем сам пост
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Пост удален'})


@app.route('/edit_post/<int:post_id>', methods=['POST'])
@login_required
def edit_post(post_id):
    """Редактирование текста поста"""
    data = request.get_json() or {}
    new_content = data.get('content', '').strip()

    if not new_content:
        return jsonify({'success': False, 'message': 'Текст поста не может быть пустым'}), 400

    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE posts SET content = ? WHERE id = ? AND author_id = ?',
                   (new_content, post_id, session['user_id']))

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Пост не найден'}), 404

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Пост обновлен'})


@app.route('/get_post/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    """Получить данные поста для редактирования"""
    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT id, content FROM posts WHERE id = ? AND author_id = ?',
                   (post_id, session['user_id']))
    post = cursor.fetchone()
    conn.close()

    if not post:
        return jsonify({'success': False, 'message': 'Пост не найден'}), 404

    return jsonify({'success': True, 'content': post['content']})


if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    print("\n" + "=" * 40)
    print("  VEGA - Социальная сеть")
    print("  http://127.0.0.1:5000")
    print("=" * 40 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)