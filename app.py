from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
from functools import wraps
import os
import random
import sqlite3
import secrets
import re
from werkzeug.utils import secure_filename
from auth import VegaAuth
from profile import VegaProfile
from events import VegaEvents

app = Flask(__name__)
app.secret_key = 'vega_secret_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.jinja_env.globals.update(zip=zip)

# Настройки загрузки файлов
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'avi', 'mov'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024


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


def init_settings_table():
    """Создание таблицы настроек пользователя"""
    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            privacy_profile TEXT DEFAULT 'all',
            privacy_messages TEXT DEFAULT 'all',
            privacy_online INTEGER DEFAULT 1,
            theme TEXT DEFAULT 'dark',
            font_size_px INTEGER DEFAULT 14,
            accent_color TEXT DEFAULT '#9d7be8',
            feed_sort TEXT DEFAULT 'newest',
            posts_per_page INTEGER DEFAULT 20,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()


init_settings_table()


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
    """Генерация гороскопа для указанного знака"""
    return profile_manager.get_daily_horoscope(zodiac)


def get_user_settings_from_db(user_id):
    """Получить настройки пользователя из БД"""
    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
    settings = cursor.fetchone()
    conn.close()

    if settings:
        return dict(settings)
    return {
        'user_id': user_id,
        'privacy_profile': 'all',
        'privacy_messages': 'all',
        'privacy_online': 1,
        'theme': 'dark',
        'font_size_px': 14,
        'accent_color': '#9d7be8',
        'feed_sort': 'newest',
        'posts_per_page': 20
    }


def save_user_settings_to_db(user_id, data):
    """Сохранить настройки пользователя в БД"""
    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO user_settings 
        (user_id, privacy_profile, privacy_messages, privacy_online, theme, 
         font_size_px, accent_color, feed_sort, posts_per_page, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        data.get('privacy_profile', 'all'),
        data.get('privacy_messages', 'all'),
        1 if data.get('privacy_online') == 'on' else 0,
        data.get('theme', 'dark'),
        int(data.get('font_size_px', 14)),
        data.get('accent_color', '#9d7be8'),
        data.get('feed_sort', 'newest'),
        int(data.get('posts_per_page', 20)),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    return True


def load_settings_to_session(user_id):
    """Загрузить настройки из БД в сессию"""
    settings = get_user_settings_from_db(user_id)
    session['privacy_profile'] = settings.get('privacy_profile', 'all')
    session['privacy_messages'] = settings.get('privacy_messages', 'all')
    session['privacy_online'] = settings.get('privacy_online', 1)
    session['theme'] = settings.get('theme', 'dark')
    session['font_size_px'] = settings.get('font_size_px', 14)
    session['accent_color'] = settings.get('accent_color', '#9d7be8')
    session['feed_sort'] = settings.get('feed_sort', 'newest')
    session['posts_per_page'] = settings.get('posts_per_page', 20)


@app.before_request
def before_request_apply_settings():
    """Применяем настройки перед каждым запросом"""
    if request.path.startswith('/static') or request.path in ['/login', '/register']:
        return
    if 'user_id' in session:
        load_settings_to_session(session['user_id'])

        if request.endpoint and request.endpoint != 'logout':
            conn = sqlite3.connect('vega.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET status = ? WHERE id = ?', ('online', session['user_id']))
            conn.commit()
            conn.close()


@app.context_processor
def inject_settings():
    """Передаём настройки во все шаблоны"""
    return {
        'user_settings': {
            'theme': session.get('theme', 'dark'),
            'font_size_px': session.get('font_size_px', 14),
            'accent_color': session.get('accent_color', '#9d7be8')
        }
    }


# ====================== МАРШРУТЫ ======================

@app.route('/')
@login_required
def index():
    session.permanent = True
    user = auth.get_user_by_id(session['user_id'])
    posts_list = auth.get_posts()

    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gallery ORDER BY created_at DESC')
    all_gallery_items = [dict(item) for item in cursor.fetchall()]
    conn.close()

    for post in posts_list:
        post['files'] = [item['file_path'] for item in all_gallery_items if item.get('post_id') == post['id']]

    real_friends = auth.get_friends(session['user_id'])

    online_friends = []
    offline_friends = []

    for f in real_friends:
        conn2 = sqlite3.connect('vega.db')
        cursor2 = conn2.cursor()
        cursor2.execute('SELECT privacy_online FROM user_settings WHERE user_id = ?', (f['id'],))
        setting = cursor2.fetchone()
        conn2.close()

        if setting and setting[0] == 0:
            f_display = f.copy()
            f_display['status'] = 'offline'
            offline_friends.append(f_display)
        else:
            if f.get('status') == 'online':
                online_friends.append(f)
            else:
                offline_friends.append(f)

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
        if 'guest' in request.form:
            guest_user = auth.guest_login()
            session['user_id'] = guest_user['id']
            session['is_guest'] = True
            session['csrf_token'] = secrets.token_hex(16)
            flash('Вы вошли как гость. Ваши действия не сохранятся.', 'info')
            return redirect(url_for('index'))

        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not phone or not password:
            flash('Заполните все поля', 'error')
        else:
            success, message, user = auth.login_by_phone(phone, password, request.remote_addr)
            if success and user:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['is_guest'] = False
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
            request.form.get('phone', '').strip(),
            request.form.get('password', '').strip(),
            request.form.get('password_confirm', '').strip(),
            request.form.get('zodiac', 'Лев')
        )
        if success and user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['is_guest'] = False
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


@app.route('/user/<int:user_id>')
@login_required
def view_user_profile(user_id):
    if user_id == session['user_id']:
        return redirect(url_for('profile_page'))

    user = auth.get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('index'))

    privacy_setting = session.get('privacy_profile', 'all')
    friend_status = auth.get_friend_status(session['user_id'], user_id)

    if privacy_setting == 'only_me':
        flash('Этот профиль скрыт владельцем', 'error')
        return redirect(url_for('index'))

    if privacy_setting == 'friends' and friend_status != 'friends':
        flash('Профиль доступен только друзьям', 'error')
        return redirect(url_for('index'))

    user_posts = auth.get_user_posts(user_id)

    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gallery ORDER BY created_at DESC')
    all_gallery_items = [dict(item) for item in cursor.fetchall()]
    conn.close()

    for post in user_posts:
        post['files'] = [item['file_path'] for item in all_gallery_items if item.get('post_id') == post['id']]

    mutual_friends = auth.get_mutual_friends(session['user_id'], user_id)
    stats = profile_manager.get_user_stats(user_id)
    horoscope = generate_random_horoscope(user.get('zodiac', 'Лев'))

    return render_template('user_profile.html',
                           profile_user=user,
                           current_user=auth.get_user_by_id(session['user_id']),
                           posts=user_posts,
                           stats=stats,
                           horoscope=horoscope,
                           friend_status=friend_status,
                           mutual_friends=mutual_friends,
                           all_items=all_gallery_items,
                           notification_count=0)


@app.route('/profile')
@login_required
def profile_page():
    user = auth.get_user_by_id(session['user_id'])
    stats = profile_manager.get_user_stats(session['user_id'])
    user_posts = auth.get_user_posts(session['user_id'])

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


@app.route('/chat')
@login_required
def chat_page():
    user = auth.get_user_by_id(session['user_id'])
    chats = auth.get_chat_users(session['user_id'])
    unread_count = auth.get_unread_count(session['user_id'])

    selected_user_id = request.args.get('user', type=int)
    selected_user = None
    messages = []

    if selected_user_id:
        selected_user = auth.get_user_by_id(selected_user_id)
        if selected_user:
            conn = sqlite3.connect('vega.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT privacy_messages FROM user_settings WHERE user_id = ?', (selected_user_id,))
            setting = cursor.fetchone()
            conn.close()

            if setting and setting['privacy_messages'] == 'friends':
                friend_status = auth.get_friend_status(session['user_id'], selected_user_id)
                if friend_status != 'friends':
                    flash('Вы не можете писать этому пользователю (только друзья)', 'error')
                    selected_user = None
                    messages = []

            if selected_user:
                messages = auth.get_messages(session['user_id'], selected_user_id)

    return render_template('chat.html',
                           current_user=user,
                           chats=chats,
                           messages=messages,
                           selected_user=selected_user,
                           unread_count=unread_count,
                           notification_count=unread_count)


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json() or {}
    to_user_id = data.get('to_user_id')
    message = data.get('message', '').strip()

    if not to_user_id:
        return jsonify({'success': False, 'error': 'Получатель не указан'})

    if not message:
        return jsonify({'success': False, 'error': 'Сообщение не может быть пустым'})

    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT privacy_messages FROM user_settings WHERE user_id = ?', (to_user_id,))
    target_settings = cursor.fetchone()
    conn.close()

    if target_settings and target_settings['privacy_messages'] == 'friends':
        friend_status = auth.get_friend_status(session['user_id'], to_user_id)
        if friend_status != 'friends':
            return jsonify({'success': False, 'error': 'Этот пользователь принимает сообщения только от друзей'})

    success, msg, message_id = auth.send_message(session['user_id'], to_user_id, message)

    if success:
        return jsonify({
            'success': True,
            'message': msg,
            'message_id': message_id,
            'data': {
                'id': message_id,
                'from_user_id': session['user_id'],
                'to_user_id': to_user_id,
                'message': message,
                'created_at': datetime.now().isoformat()
            }
        })
    else:
        return jsonify({'success': False, 'error': msg})


@app.route('/get_messages/<int:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    messages = auth.get_messages(session['user_id'], user_id)
    return jsonify({'success': True, 'messages': messages})


@app.route('/get_chats_list', methods=['GET'])
@login_required
def get_chats_list():
    """Получить список чатов для AJAX"""
    chats = auth.get_chat_users(session['user_id'])
    return jsonify({'success': True, 'chats': chats})


@app.route('/get_unread_count', methods=['GET'])
@login_required
def get_unread_count():
    count = auth.get_unread_count(session['user_id'])
    return jsonify({'success': True, 'count': count})


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.form.get('csrf_token') != session.get('csrf_token'):
        flash('Ошибка безопасности. Попробуйте снова.', 'error')
        return redirect(url_for('profile_page'))

    data = {k: request.form.get(k, '').strip() for k in ['name', 'bio', 'city', 'phone', 'birthday', 'zodiac']}
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
        success, message = profile_manager.update_avatar(session['user_id'], url)
        flash(message, 'success' if success else 'error')
    return redirect(url_for('profile_page'))


@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Загрузка аватара через файл"""
    if 'avatar' not in request.files:
        flash('Файл не выбран', 'error')
        return redirect(url_for('profile_page'))

    file = request.files['avatar']
    if file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('profile_page'))

    if file and allowed_file(file.filename):
        if not file.content_type.startswith('image/'):
            flash('Можно загружать только изображения', 'error')
            return redirect(url_for('profile_page'))

        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"avatar_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        avatar_url = f'/static/uploads/{filename}'
        success, message = profile_manager.update_avatar(session['user_id'], avatar_url)
        flash(message, 'success' if success else 'error')
    else:
        flash('Недопустимый формат файла. Поддерживаются: PNG, JPG, JPEG, GIF, WEBP', 'error')

    return redirect(url_for('profile_page'))


# ====================== AJAX МАРШРУТЫ ДЛЯ НАСТРОЕК ======================

@app.route('/save_settings', methods=['POST'])
@login_required
def save_settings():
    if request.form.get('csrf_token') != session.get('csrf_token'):
        return jsonify({'success': False, 'message': 'Ошибка безопасности'})

    save_user_settings_to_db(session['user_id'], request.form)
    load_settings_to_session(session['user_id'])

    return jsonify({'success': True, 'message': 'Настройки сохранены!'})


@app.route('/save_theme_ajax', methods=['POST'])
@login_required
def save_theme_ajax():
    """Сохранение темы через AJAX"""
    data = request.get_json() or {}
    theme = data.get('theme', 'dark')

    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, theme, updated_at)
        VALUES (?, ?, ?)
    ''', (session['user_id'], theme, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    session['theme'] = theme

    return jsonify({'success': True, 'message': 'Тема изменена!', 'theme': theme})


@app.route('/save_font_size_ajax', methods=['POST'])
@login_required
def save_font_size_ajax():
    """Сохранение размера шрифта через AJAX"""
    data = request.get_json() or {}
    font_size_px = data.get('font_size_px', 14)

    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, font_size_px, updated_at)
        VALUES (?, ?, ?)
    ''', (session['user_id'], font_size_px, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    session['font_size_px'] = font_size_px

    return jsonify({'success': True, 'message': 'Размер шрифта изменён!', 'font_size_px': font_size_px})


@app.route('/save_accent_color_ajax', methods=['POST'])
@login_required
def save_accent_color_ajax():
    """Сохранение акцентного цвета через AJAX"""
    data = request.get_json() or {}
    color = data.get('color', '#9d7be8')

    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, accent_color, updated_at)
        VALUES (?, ?, ?)
    ''', (session['user_id'], color, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    session['accent_color'] = color

    return jsonify({'success': True, 'message': 'Цвет интерфейса изменён!', 'color': color})


@app.route('/save_privacy_ajax', methods=['POST'])
@login_required
def save_privacy_ajax():
    """Сохранение настроек приватности через AJAX"""
    data = request.get_json() or {}
    privacy_profile = data.get('privacy_profile', 'all')
    privacy_messages = data.get('privacy_messages', 'all')
    privacy_online = 1 if data.get('privacy_online') else 0

    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, privacy_profile, privacy_messages, privacy_online, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], privacy_profile, privacy_messages, privacy_online, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    session['privacy_profile'] = privacy_profile
    session['privacy_messages'] = privacy_messages
    session['privacy_online'] = privacy_online

    return jsonify({'success': True, 'message': 'Настройки приватности сохранены!'})


@app.route('/save_feed_ajax', methods=['POST'])
@login_required
def save_feed_ajax():
    """Сохранение настроек ленты через AJAX"""
    data = request.get_json() or {}
    feed_sort = data.get('feed_sort', 'newest')
    posts_per_page = data.get('posts_per_page', 20)

    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, feed_sort, posts_per_page, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], feed_sort, posts_per_page, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    session['feed_sort'] = feed_sort
    session['posts_per_page'] = posts_per_page

    return jsonify({'success': True, 'message': 'Настройки ленты сохранены!'})


# ====================== ОСНОВНЫЕ МАРШРУТЫ ======================

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
    settings = get_user_settings_from_db(session['user_id'])
    return render_template('settings.html', current_user=user, settings=settings, notification_count=0)


@app.route('/about')
@login_required
def about_page():
    user = auth.get_user_by_id(session['user_id'])
    return render_template('about.html', current_user=user)


@app.route('/team')
@login_required
def team_page():
    user = auth.get_user_by_id(session['user_id'])
    return render_template('team.html', current_user=user)


@app.route('/privacy')
@login_required
def privacy_page():
    user = auth.get_user_by_id(session['user_id'])
    return render_template('privacy.html', current_user=user)


@app.route('/terms')
@login_required
def terms_page():
    user = auth.get_user_by_id(session['user_id'])
    return render_template('terms.html', current_user=user)


@app.route('/contacts')
@login_required
def contacts_page():
    user = auth.get_user_by_id(session['user_id'])
    return render_template('contacts.html', current_user=user)


@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
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
    try:
        success, message, new_count, action = auth.like_post(session['user_id'], post_id)
        return jsonify({
            'success': success,
            'message': message,
            'new_count': new_count,
            'action': action
        })
    except Exception as e:
        print(f"Error in like_post: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'new_count': 0,
            'action': 'error'
        })


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if session.get('is_guest'):
        flash('Гостевой аккаунт не может менять пароль', 'error')
        return redirect(url_for('settings_page'))

    if request.form.get('csrf_token') != session.get('csrf_token'):
        flash('Ошибка безопасности. Попробуйте снова.', 'error')
        return redirect(url_for('settings_page'))

    old_password = request.form.get('old_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    if not old_password or not new_password or not confirm_password:
        flash('Заполните все поля', 'error')
        return redirect(url_for('settings_page'))

    if len(new_password) < 6:
        flash('Новый пароль должен содержать минимум 6 символов', 'error')
        return redirect(url_for('settings_page'))

    if new_password != confirm_password:
        flash('Новые пароли не совпадают', 'error')
        return redirect(url_for('settings_page'))

    success, message = auth.change_password(session['user_id'], old_password, new_password, confirm_password)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('settings_page'))


@app.route('/get_comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    try:
        conn = sqlite3.connect('vega.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT comments.*, users.name as author_name, users.avatar as author_avatar
            FROM comments 
            JOIN users ON comments.user_id = users.id 
            WHERE comments.post_id = ?
            ORDER BY comments.created_at ASC
        ''', (post_id,))

        comments = [dict(c) for c in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'comments': comments})
    except Exception as e:
        print(f"Error getting comments: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    try:
        data = request.get_json() or {}
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'success': False, 'error': 'Комментарий не может быть пустым'})

        if session.get('is_guest'):
            return jsonify({'success': False, 'error': 'Гости не могут оставлять комментарии'})

        conn = sqlite3.connect('vega.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO comments (user_id, post_id, content, created_at)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], post_id, content, datetime.now().isoformat()))

        cursor.execute('UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?', (post_id,))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Комментарий добавлен'})
    except Exception as e:
        print(f"Error adding comment: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/get_user_likes', methods=['GET'])
@login_required
def get_user_likes():
    try:
        conn = sqlite3.connect('vega.db')
        cursor = conn.cursor()
        cursor.execute('SELECT post_id FROM likes WHERE user_id = ?', (session['user_id'],))
        liked_posts = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'liked_posts': liked_posts})
    except Exception as e:
        print(f"Error in get_user_likes: {e}")
        return jsonify({'success': False, 'liked_posts': []})


@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    conn = sqlite3.connect('vega.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM posts WHERE id = ? AND author_id = ?', (post_id, session['user_id']))
    post = cursor.fetchone()

    if not post:
        conn.close()
        return jsonify({'success': False, 'message': 'Пост не найден'}), 404

    cursor.execute('SELECT file_path FROM gallery WHERE post_id = ?', (post_id,))
    files = cursor.fetchall()
    for file in files:
        file_path = file[0].lstrip('/')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

    cursor.execute('DELETE FROM gallery WHERE post_id = ?', (post_id,))
    cursor.execute('DELETE FROM likes WHERE post_id = ?', (post_id,))
    cursor.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Пост удален'})


@app.route('/edit_post/<int:post_id>', methods=['POST'])
@login_required
def edit_post(post_id):
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


@app.route('/post/<int:post_id>')
@login_required
def view_post(post_id):
    """Просмотр отдельного поста"""
    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            posts.*,
            users.id as author_id,
            users.name as author_name,
            users.avatar as author_avatar,
            users.zodiac as author_zodiac
        FROM posts 
        JOIN users ON posts.author_id = users.id 
        WHERE posts.id = ?
    ''', (post_id,))

    post = cursor.fetchone()

    if not post:
        conn.close()
        flash('Пост не найден', 'error')
        return redirect(url_for('index'))

    cursor.execute('SELECT * FROM gallery WHERE post_id = ?', (post_id,))
    gallery_items = [dict(item) for item in cursor.fetchall()]

    cursor.execute('''
        SELECT comments.*, users.name as author_name, users.avatar as author_avatar
        FROM comments 
        JOIN users ON comments.user_id = users.id 
        WHERE comments.post_id = ?
        ORDER BY comments.created_at DESC
    ''', (post_id,))
    comments = [dict(c) for c in cursor.fetchall()]

    conn.close()

    post_dict = dict(post)
    post_dict['author'] = {
        'id': post_dict['author_id'],
        'name': post_dict['author_name'],
        'avatar': post_dict['author_avatar'],
        'zodiac': post_dict.get('author_zodiac', 'Лев')
    }
    post_dict['files'] = [item['file_path'] for item in gallery_items]

    return render_template('single_post.html',
                           post=post_dict,
                           comments=comments,
                           current_user=auth.get_user_by_id(session['user_id']))


@app.route('/repost/<int:post_id>', methods=['POST'])
@login_required
def repost_to_wall(post_id):
    """Репост поста на свою стену"""
    if session.get('is_guest'):
        return jsonify({'success': False, 'message': 'Гости не могут делать репосты'})

    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT posts.*, users.name as author_name, users.avatar as author_avatar
        FROM posts 
        JOIN users ON posts.author_id = users.id 
        WHERE posts.id = ?
    ''', (post_id,))
    original_post = cursor.fetchone()

    if not original_post:
        conn.close()
        return jsonify({'success': False, 'message': 'Пост не найден'})

    cursor.execute('SELECT file_path, file_type FROM gallery WHERE post_id = ?', (post_id,))
    gallery_items = cursor.fetchall()

    repost_content = f'''<div class="shared-post">
    <div class="shared-header">
        <img src="{original_post['author_avatar']}" style="width:20px;height:20px;border-radius:50%;">
        <strong>{original_post['author_name']}</strong>
    </div>
    <div>{original_post['content'] if original_post['content'] else ''}</div>'''

    for item in gallery_items:
        if item['file_type'] == 'image':
            repost_content += f'''<div style="margin-top:10px;">
                <img src="{item['file_path']}" style="max-width:100%;border-radius:12px;margin-top:8px;">
            </div>'''
        else:
            repost_content += f'''<div style="margin-top:10px;">
                <video controls style="max-width:100%;border-radius:12px;"><source src="{item['file_path']}"></video>
            </div>'''

    repost_content += '</div>'

    cursor.execute('''
        INSERT INTO posts (author_id, content, image, privacy, is_repost, original_author_id, created_at)
        VALUES (?, ?, ?, 'public', 1, ?, ?)
    ''', (
        session['user_id'],
        repost_content,
        None,
        original_post['author_id'],
        datetime.now().isoformat()
    ))

    cursor.execute('UPDATE posts SET shares = shares + 1 WHERE id = ?', (post_id,))

    for item in gallery_items:
        cursor.execute('''
            INSERT INTO gallery (user_id, file_path, file_type, caption, post_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            item['file_path'],
            item['file_type'],
            f'Репост: {original_post["content"][:50] if original_post["content"] else ""}',
            cursor.lastrowid,
            datetime.now().isoformat()
        ))

    conn.commit()

    cursor.execute('SELECT shares FROM posts WHERE id = ?', (post_id,))
    result = cursor.fetchone()
    new_count = result['shares'] if result else 0

    conn.close()
    return jsonify({'success': True, 'message': 'Репост опубликован!', 'new_count': new_count})


@app.route('/share_to_friend', methods=['POST'])
@login_required
def share_to_friend():
    """Отправить репост другу в чат"""
    if session.get('is_guest'):
        return jsonify({'success': False, 'message': 'Гости не могут отправлять репосты'})

    data = request.get_json() or {}
    post_id = data.get('post_id')
    friend_id = data.get('friend_id')

    if not post_id or not friend_id:
        return jsonify({'success': False, 'message': 'Недостаточно данных'})

    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT name FROM users WHERE id = ?', (session['user_id'],))
    current_user_data = cursor.fetchone()
    current_user_name = current_user_data['name'] if current_user_data else 'Пользователь'

    cursor.execute('''
        SELECT posts.*, users.name as author_name, users.avatar as author_avatar
        FROM posts 
        JOIN users ON posts.author_id = users.id 
        WHERE posts.id = ?
    ''', (post_id,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        return jsonify({'success': False, 'message': 'Пост не найден'})

    cursor.execute('SELECT file_path, file_type FROM gallery WHERE post_id = ?', (post_id,))
    gallery_items = cursor.fetchall()

    def clean_html(text):
        if not text:
            return ''
        import re
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        text = ' '.join(text.split())
        return text.strip()

    clean_content = clean_html(post['content'])

    message_text = f"""📢 РЕПОСТ ОТ {post['author_name'].upper()}

{clean_content if clean_content else '(пост без текста)'}

"""

    if gallery_items:
        message_text += f"\n📎 В посте {len(gallery_items)} вложени(й):\n"
        for idx, item in enumerate(gallery_items, 1):
            if item['file_type'] == 'image':
                message_text += f"  📷 Фото {idx}\n"
            else:
                message_text += f"  🎬 Видео {idx}\n"

    message_text += f"\n━━━━━━━━━━━━━━━━━━━━\n🔄 Поделился(ась): {current_user_name}"
    message_text += f"\n💬 Ответить в чате: /chat?user={session['user_id']}"

    cursor.execute('''
        INSERT INTO messages (from_user_id, to_user_id, message, created_at)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], friend_id, message_text, datetime.now().isoformat()))

    cursor.execute('UPDATE posts SET shares = shares + 1 WHERE id = ?', (post_id,))

    conn.commit()

    cursor.execute('SELECT shares FROM posts WHERE id = ?', (post_id,))
    result = cursor.fetchone()
    new_count = result['shares'] if result else 0

    conn.close()
    return jsonify({'success': True, 'message': 'Репост отправлен!', 'new_count': new_count})


@app.route('/get_friends_list', methods=['GET'])
@login_required
def get_friends_list():
    friends = auth.get_friends(session['user_id'])

    filtered_friends = []
    for friend in friends:
        conn = sqlite3.connect('vega.db')
        cursor = conn.cursor()
        cursor.execute('SELECT privacy_online FROM user_settings WHERE user_id = ?', (friend['id'],))
        setting = cursor.fetchone()
        conn.close()

        if setting and setting[0] == 0:
            friend_display = friend.copy()
            friend_display['status'] = 'offline'
            filtered_friends.append(friend_display)
        else:
            filtered_friends.append(friend)

    return jsonify({
        'success': True,
        'friends': filtered_friends
    })


@app.route('/search', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'success': True, 'results': []})

    results = profile_manager.search_users(query, limit=10)
    return jsonify({'success': True, 'results': results})


if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    print("\n" + "=" * 40)
    print("  VEGA - Социальная сеть")
    print("  http://127.0.0.1:5000")
    print("=" * 40 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)