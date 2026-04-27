from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
from functools import wraps
import os
import hashlib  # Для хеширования паролей

app = Flask(__name__)
app.secret_key = 'vega_secret_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# ======================
# РАБОТА С БАЗОЙ ДАННЫХ
# ======================
import sqlite3

def get_db():
    """Подключение к базе данных"""
    conn = sqlite3.connect('vega.db')
    conn.row_factory = sqlite3.Row  # чтобы можно было получать данные по ключу
    return conn

def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Создание таблиц, если их нет"""
    conn = get_db()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT DEFAULT 'https://randomuser.me/api/portraits/men/32.jpg',
            cover TEXT DEFAULT '',
            zodiac TEXT DEFAULT 'Лев',
            birthday TEXT DEFAULT '',
            city TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            status TEXT DEFAULT 'online',
            friends_count INTEGER DEFAULT 0,
            subscribers INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица постов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            image TEXT DEFAULT '',
            privacy TEXT DEFAULT 'public',
            likes INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Таблица лайков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')

    # Таблица комментариев
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')

    # Таблица репостов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ База данных готова!")

# Запускаем создание таблиц при старте
init_db()

# ======================
# ДЕКОРАТОР ДЛЯ ПРОВЕРКИ АВТОРИЗАЦИИ
# ======================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'info')
            return redirect(url_for('login'))

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()

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
# ГЛАВНАЯ СТРАНИЦА (ЛЕНТА)
# ======================
@app.route('/')
@login_required
def index():
    session.permanent = True

    conn = get_db()

    # Текущий пользователь
    current_user = conn.execute('SELECT * FROM users WHERE id = ?',
                                (session['user_id'],)).fetchone()

    # Все посты с информацией об авторах
    posts = conn.execute('''
                SELECT posts.*, users.name as author_name, users.avatar as author_avatar,
                       users.zodiac as author_zodiac
                FROM posts
                JOIN users ON posts.user_id = users.id
                ORDER BY posts.created_at DESC
            ''').fetchall()

    conn.close()

    return render_template('index.html',
                           current_user=current_user,
                           posts=posts)

# ======================
# АВТОРИЗАЦИЯ
# ======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Заполните все поля', 'error')
            return render_template('login.html')

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?',
                            (email, hash_password(password))).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session.permanent = True
            flash(f'С возвращением, {user["name"]}! ✨', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()
        zodiac = request.form.get('zodiac', 'Лев')

        # Валидация данных
        if not name or not email or not password:
            flash('Заполните все обязательные поля', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('register.html')

        if password != password_confirm:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        conn = get_db()

        try:
            # Проверяем, нет ли уже такого email
            existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing:
                conn.close()
                flash('Пользователь с таким email уже существует', 'error')
                return render_template('register.html')

            # Создаём пользователя с хешированным паролем
            hashed_password = hash_password(password)
            cursor = conn.execute('''
                INSERT INTO users (name, email, password, zodiac)
                VALUES (?, ?, ?, ?)
            ''', (name, email, hashed_password, zodiac))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            session['user_id'] = user_id
            session['user_name'] = name
            session.permanent = True

            flash(f'Добро пожаловать, {name}! ✨', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            conn.rollback()
            flash('Произошла ошибка при регистрации', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('login'))

# ======================
# ПРОФИЛЬ
# ======================
@app.route('/profile')
@login_required
def profile():
    conn = get_db()
    current_user = conn.execute('SELECT * FROM users WHERE id = ?',
                        (session['user_id'],)).fetchone()

    # Посты пользователя
    posts = conn.execute('''
        SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()

    # Получаем количество постов через SQL-запрос
    posts_count = conn.execute('SELECT COUNT(*) FROM posts WHERE user_id = ?',
                              (session['user_id'],)).fetchone()[0]

    conn.close()

    # Гороскоп
    zodiac = current_user['zodiac'] or 'Лев'
    horoscope = {
        'name': zodiac,
        'emoji': '♌' if zodiac == 'Лев' else '♓' if zodiac == 'Рыбы' else '⭐',
        'element': 'Огонь',
        'planet': 'Солнце',
        'date_range': '23 июля - 22 августа',
        'today_horoscope': 'Сегодня звёзды благоволят вашему знаку! Отличный день для новых начинаний.',
        'love_horoscope': 'В личной жизни наступает гармоничный период.',
        'career_horoscope': 'На работе вас ждёт признание.',
        'lucky_numbers': [1, 8, 15, 23, 42],
        'lucky_color': 'Золотой',
        'compatibility': ['Овен', 'Стрелец', 'Близнецы']
    }

    return render_template('profile.html',
                   current_user=current_user,
                   posts=posts,
                   horoscope=horoscope,
                   stats={'posts_count': posts_count})

# ======================
# ОБНОВЛЕНИЕ ПРОФИЛЯ
# ======================
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    birthday = request.form.get('birthday', '').strip()
    zodiac = request.form.get('zodiac', '').strip()
    city = request.form.get('city', '').strip()
    phone = request.form.get('phone', '').strip()
    bio = request.form.get('bio', '').strip()

    conn = get_db()
    try:
        conn.execute('''
            UPDATE users
            SET name = ?, birthday = ?, zodiac = ?, city = ?, phone = ?, bio = ?
            WHERE id = ?
        ''', (name, birthday, zodiac, city, phone, bio, session['user_id']))
        conn.commit()
        conn.close()
        session['user_name'] = name
        flash('Профиль успешно обновлён! ✨', 'success')
    except Exception as e:
        flash('Ошибка при обновлении профиля', 'error')
    return redirect(url_for('profile'))

@app.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    avatar_url = request.form.get('avatar_url', '').strip()

    if avatar_url:
        conn = get_db()
        try:
            conn.execute('UPDATE users SET avatar = ? WHERE id = ?',
                     (avatar_url, session['user_id']))
            conn.commit()
            conn.close()
            flash('Аватар обновлён! 📸 ', 'success')
        except Exception as e:
            flash('Ошибка при обновлении аватара', 'error')

    return redirect(url_for('profile'))

# ======================
# ПОСТЫ
# ======================
@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content', '').strip()
    image = request.form.get('image', '').strip()
    privacy = request.form.get('privacy', 'public')

    if not content:
        flash('Пост не может быть пустым', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO posts (user_id, content, image, privacy)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], content, image, privacy))
        conn.commit()
        conn.close()
        flash('Пост опубликован! ✨', 'success')
    except Exception as e:
        flash('Ошибка при публикации поста', 'error')
    return redirect(url_for('index'))

# ======================
# ЛАЙКИ
# ======================
@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    conn = get_db()

    try:
        # Проверяем, лайкал ли уже
        existing = conn.execute('SELECT id FROM likes WHERE user_id = ? AND post_id = ?',
                            (session['user_id'], post_id)).fetchone()

        if existing:
            # Убираем лайк
            conn.execute('DELETE FROM likes WHERE user_id = ? AND post_id = ?',
                 (session['user_id'], post_id))
            conn.execute('UPDATE posts SET likes = likes - 1 WHERE id = ?', (post_id,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'action': 'unliked', 'message': 'Лайк убран'})
        else:
            # Ставим лайк
            conn.            execute('INSERT INTO likes (user_id, post_id) VALUES (?, ?)',
                (session['user_id'], post_id))
            conn.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'action': 'liked', 'message': 'Лайк поставлен! ✨'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'error': 'Ошибка при обработке лайка'}), 500

# ======================
# КОММЕНТАРИИ
# ======================
@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    data = request.get_json() or {}
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'success': False, 'error': 'Комментарий не может быть пустым'}), 400

    conn = get_db()
    try:
        conn.execute('INSERT INTO comments (user_id, post_id, content) VALUES (?, ?, ?)',
                    (session['user_id'], post_id, content))
        conn.execute('UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?', (post_id,))
        conn.commit()
        # Получаем информацию о комментарии для возврата
        comment = conn.execute('''
            SELECT c.*, u.name as author_name, u.avatar as author_avatar
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = (SELECT last_insert_rowid())
        ''').fetchone()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Комментарий добавлен! 💬',
            'comment': {
                'id': comment['id'],
                'content': comment['content'],
                'author_name': comment['author_name'],
                'author_avatar': comment['author_avatar'],
                'created_at': comment['created_at']
            }
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'error': 'Ошибка при добавлении комментария'}), 500

# ======================
# РЕПОСТЫ
# ======================
@app.route('/share_post/<int:post_id>', methods=['POST'])
@login_required
def share_post(post_id):
    conn = get_db()
    try:
        # Проверяем, не репостил ли уже
        existing = conn.execute('SELECT id FROM shares WHERE user_id = ? AND post_id = ?',
                            (session['user_id'], post_id)).fetchone()
        if existing:
            conn.close()
            return jsonify({'success': False, 'error': 'Вы уже репостили этот пост'}), 400

        conn.execute('INSERT INTO shares (user_id, post_id) VALUES (?, ?)',
                    (session['user_id'], post_id))
        conn.execute('UPDATE posts SET shares = shares + 1 WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Пост опубликован на вашей странице! 🔄'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'error': 'Ошибка при репосте'}), 500

# ======================
# НАСТРОЙКИ
# ======================
@app.route('/settings')
@login_required
def settings():
    conn = get_db()
    current_user = conn.execute('SELECT * FROM users WHERE id = ?',
                        (session['user_id'],)).fetchone()
    conn.close()
    return render_template('settings.html', current_user=current_user)

# ======================
# ЗАПУСК
# ======================
if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  VEGA - Астрологическая социальная сеть")
    print("=" * 50)
    print("  Сервер: http://127.0.0.1:5000")
    print("  Вход:   http://127.0.0.1:5000/login")
    print("=" * 50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
