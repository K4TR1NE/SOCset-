import sqlite3
import re
import os
from datetime import datetime, timedelta


class VegaAuth:
    """Класс для работы с авторизацией и регистрацией"""

    def __init__(self, db_name='vega.db'):
        """Инициализация подключения к БД"""
        self.db_name = db_name
        self.init_database()

    def change_password(self, user_id, old_password, new_password, confirm_password):
        """Смена пароля"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем текущий пароль пользователя
        cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return False, "Пользователь не найден"

        # Проверяем старый пароль
        if user[0] != old_password:
            conn.close()
            return False, "Старый пароль неверен"

        # Проверяем длину нового пароля
        if len(new_password) < 6:
            conn.close()
            return False, "Новый пароль должен содержать минимум 6 символов"

        # Проверяем совпадение
        if new_password != confirm_password:
            conn.close()
            return False, "Новые пароли не совпадают"

        # Обновляем пароль
        cursor.execute('UPDATE users SET password = ?, updated_at = ? WHERE id = ?',
                       (new_password, datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()

        return True, "Пароль успешно изменен!"

    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Создание таблиц в БД"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                avatar TEXT DEFAULT 'https://randomuser.me/api/portraits/men/32.jpg',
                cover TEXT DEFAULT 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d',
                zodiac TEXT DEFAULT 'Лев',
                bio TEXT DEFAULT '',
                city TEXT DEFAULT '',
                birthday TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                website TEXT DEFAULT '',
                vk_link TEXT DEFAULT '',
                telegram_link TEXT DEFAULT '',
                status TEXT DEFAULT 'offline',
                friends_count INTEGER DEFAULT 0,
                subscribers INTEGER DEFAULT 0,
                is_guest INTEGER DEFAULT 0,
                email_verified INTEGER DEFAULT 0,
                profile_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                image TEXT,
                likes INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                privacy TEXT DEFAULT 'public',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (friend_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')

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

        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")

    def guest_login(self):
        """Создание гостевого аккаунта"""
        conn = self.get_connection()
        cursor = conn.cursor()

        import random
        guest_name = f"Гость_{random.randint(1000, 9999)}"
        guest_phone = f"guest_{random.randint(100000, 999999)}"
        guest_password = f"guest_{random.randint(100000, 999999)}"

        cursor.execute('''
            INSERT INTO users (phone, password, name, zodiac, is_guest, created_at, status)
            VALUES (?, ?, ?, ?, 1, ?, 'online')
        ''', (guest_phone, guest_password, guest_name, 'Лев', datetime.now().isoformat()))

        conn.commit()
        user_id = cursor.lastrowid

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = dict(cursor.fetchone())
        conn.close()

        return user

    def validate_password(self, password):
        if len(password) < 6:
            return False, "Пароль должен содержать минимум 6 символов"
        if not re.search(r'[a-zA-Zа-яА-Я]', password):
            return False, "Пароль должен содержать хотя бы одну букву"
        if not re.search(r'\d', password):
            return False, "Пароль должен содержать хотя бы одну цифру"
        return True, "OK"

    def validate_name(self, name):
        if len(name) < 2:
            return False, "Имя должно содержать минимум 2 символа"
        if len(name) > 50:
            return False, "Имя слишком длинное"
        return True, "OK"

    def get_user_by_id(self, user_id):
        """Получить пользователя по ID (поддерживает гостей)"""
        # Если это гость (отрицательный ID)
        if user_id < 0:
            from flask import session
            guest_data = session.get('guest_data', {})
            return {
                'id': user_id,
                'name': guest_data.get('name', f'Гость_{abs(user_id)}'),
                'avatar': guest_data.get('avatar', 'https://randomuser.me/api/portraits/men/guest.jpg'),
                'zodiac': 'Лев',
                'is_guest': True,
                'email': None,
                'phone': None,
                'bio': '',
                'city': '',
                'status': 'online',
                'friends_count': 0,
                'subscribers': 0
            }

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def create_guest_session(self):
        """Создание временной гостевой сессии (без сохранения в БД)"""
        import random
        import string

        # Генерируем уникальный временный ID
        guest_id = random.randint(10000, 99999)
        guest_name = f"Гость_{guest_id}"

        # Создаем временного пользователя в сессии (не сохраняем в БД)
        guest_user = {
            'id': -guest_id,  # Отрицательный ID чтобы отличать от реальных
            'name': guest_name,
            'avatar': 'https://randomuser.me/api/portraits/men/guest.jpg',
            'zodiac': 'Лев',
            'is_guest': True,
            'email': None,
            'phone': None,
            'bio': '',
            'city': '',
            'status': 'online',
            'friends_count': 0,
            'subscribers': 0
        }

        return guest_user

    def is_guest(self, user_id):
        """Проверка, является ли пользователь гостем"""
        return user_id < 0  # Гости имеют отрицательные ID

    def register(self, name, phone, password, password_confirm, zodiac='Лев'):
        """Регистрация нового пользователя по телефону"""
        name = name.strip()
        phone = phone.strip()

        if not name or not phone or not password:
            return False, "Заполните все обязательные поля", None

        valid, msg = self.validate_name(name)
        if not valid:
            return False, msg, None

        # Валидация телефона (простая проверка)
        if len(phone) < 10:
            return False, "Некорректный номер телефона", None

        valid, msg = self.validate_password(password)
        if not valid:
            return False, msg, None

        if password != password_confirm:
            return False, "Пароли не совпадают", None

        valid_zodiacs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
                         'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        if zodiac not in valid_zodiacs:
            zodiac = 'Лев'

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Проверяем существование телефона
            cursor.execute('SELECT id FROM users WHERE phone = ?', (phone,))
            if cursor.fetchone():
                conn.close()
                return False, "Пользователь с таким номером телефона уже существует", None

            cursor.execute('''
                INSERT INTO users (phone, password, name, zodiac, created_at, is_guest)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (phone, password, name, zodiac, datetime.now().isoformat()))

            conn.commit()
            user_id = cursor.lastrowid

            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = dict(cursor.fetchone())

            conn.close()
            print(f"✅ Зарегистрирован: {name} ({phone})")
            return True, "Регистрация успешна!", user

        except Exception as e:
            conn.close()
            return False, f"Ошибка при регистрации: {str(e)}", None

    def login_by_phone(self, phone, password, ip_address=None):
        """Вход по номеру телефона"""
        phone = phone.strip()

        if not phone or not password:
            return False, "Введите телефон и пароль", None

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE phone = ?', (phone,))
        user = cursor.fetchone()

        if user is None:
            conn.close()
            return False, "Неверный телефон или пароль", None

        user_dict = dict(user)

        if user_dict['password'] != password:
            conn.close()
            return False, "Неверный телефон или пароль", None

        cursor.execute('UPDATE users SET last_login = ?, status = ? WHERE id = ?',
                       (datetime.now().isoformat(), 'online', user_dict['id']))
        conn.commit()
        conn.close()

        print(f"✅ Вход: {user_dict['name']} ({phone})")
        return True, f"Добро пожаловать, {user_dict['name']}!", user_dict

    def login(self, email, password, ip_address=None):
        email = email.strip().lower()

        if not email or not password:
            return False, "Введите email и пароль", None

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user is None:
            conn.close()
            return False, "Неверный email или пароль", None

        user_dict = dict(user)

        if user_dict['password'] != password:
            conn.close()
            return False, "Неверный email или пароль", None

        cursor.execute('UPDATE users SET last_login = ?, status = ? WHERE id = ?',
                       (datetime.now().isoformat(), 'online', user_dict['id']))
        conn.commit()
        conn.close()

        print(f"✅ Вход: {user_dict['name']} ({email})")
        return True, f"Добро пожаловать, {user_dict['name']}!", user_dict

    def logout(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = ? WHERE id = ?', ('offline', user_id))
        conn.commit()
        conn.close()
        return True

    def create_post(self, user_id, content, image=None, privacy='public'):
        """Создание поста (гости не могут создавать посты)"""
        # Гости не могут создавать посты
        if user_id < 0:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO posts (author_id, content, image, privacy)
                VALUES (?, ?, ?, ?)
            ''', (user_id, content, image, privacy))
            conn.commit()
            post_id = cursor.lastrowid
            conn.close()
            return post_id
        except Exception as e:
            conn.close()
            return None

    def get_posts(self, limit=20, offset=0):
        """Получить все посты (только от реальных пользователей)"""
        conn = self.get_connection()
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
            WHERE users.id > 0  -- Исключаем гостей
            ORDER BY posts.created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        posts = cursor.fetchall()

        posts_list = []
        for post in posts:
            post_dict = dict(post)
            post_dict['author'] = {
                'id': post_dict['author_id'],
                'name': post_dict['author_name'],
                'avatar': post_dict['author_avatar'],
                'zodiac': post_dict.get('author_zodiac', 'Лев')
            }
            posts_list.append(post_dict)

        conn.close()
        return posts_list

    def get_user_posts(self, user_id, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts WHERE author_id = ? ORDER BY created_at DESC LIMIT ?', (user_id, limit))
        posts = cursor.fetchall()
        posts_list = [dict(post) for post in posts]
        conn.close()
        return posts_list

    def like_post(self, user_id, post_id):
        """Лайк/анлайк поста - возвращает новое количество лайков и действие"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем, есть ли уже лайк
        cursor.execute('SELECT id FROM likes WHERE user_id = ? AND post_id = ?', (user_id, post_id))
        existing = cursor.fetchone()

        if existing:
            # Удаляем лайк
            cursor.execute('DELETE FROM likes WHERE user_id = ? AND post_id = ?', (user_id, post_id))
            cursor.execute('UPDATE posts SET likes = likes - 1 WHERE id = ?', (post_id,))
            conn.commit()

            # Получаем новое количество лайков
            cursor.execute('SELECT likes FROM posts WHERE id = ?', (post_id,))
            result = cursor.fetchone()
            new_count = result[0] if result else 0
            conn.close()
            return True, "Лайк удален", new_count, 'unliked'
        else:
            # Добавляем лайк
            cursor.execute('INSERT INTO likes (user_id, post_id) VALUES (?, ?)', (user_id, post_id))
            cursor.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
            conn.commit()

            # Получаем новое количество лайков
            cursor.execute('SELECT likes FROM posts WHERE id = ?', (post_id,))
            result = cursor.fetchone()
            new_count = result[0] if result else 0
            conn.close()
            return True, "Лайк добавлен", new_count, 'liked'

    def add_comment(self, user_id, post_id, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comments (user_id, post_id, content) VALUES (?, ?, ?)',
                       (user_id, post_id, content))
        cursor.execute('UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return True, "Комментарий добавлен"

    def send_friend_request(self, user_id, friend_id):
        if user_id == friend_id:
            return False, "Нельзя добавить себя в друзья"
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM users WHERE id = ?', (friend_id,))
        friend = cursor.fetchone()
        if not friend:
            conn.close()
            return False, "Пользователь не найден"
        cursor.execute('SELECT * FROM friends WHERE (user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)',
                       (user_id, friend_id, friend_id, user_id))
        existing = cursor.fetchone()
        if existing:
            if existing['status'] == 'accepted':
                conn.close()
                return False, "Вы уже друзья"
            elif existing['status'] == 'pending':
                if existing['user_id'] == user_id:
                    conn.close()
                    return False, "Заявка уже отправлена"
                else:
                    cursor.execute('UPDATE friends SET status=? WHERE id=?', ('accepted', existing['id']))
                    cursor.execute('UPDATE users SET friends_count=friends_count+1 WHERE id IN (?,?)',
                                   (user_id, friend_id))
                    conn.commit()
                    conn.close()
                    return True, f"Вы и {friend['name']} теперь друзья!"
        cursor.execute('INSERT INTO friends (user_id, friend_id, status) VALUES (?,?,?)',
                       (user_id, friend_id, 'pending'))
        conn.commit()
        conn.close()
        return True, f"Заявка отправлена {friend['name']}"

    def accept_friend_request(self, request_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM friends WHERE id=? AND friend_id=? AND status=?',
                       (request_id, user_id, 'pending'))
        req = cursor.fetchone()
        if not req:
            conn.close()
            return False, "Заявка не найдена"
        cursor.execute('UPDATE friends SET status=? WHERE id=?', ('accepted', request_id))
        cursor.execute('UPDATE users SET friends_count=friends_count+1 WHERE id IN (?,?)', (req['user_id'], user_id))
        conn.commit()
        conn.close()
        return True, "Заявка принята!"

    def decline_friend_request(self, request_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM friends WHERE id=? AND friend_id=? AND status=?', (request_id, user_id, 'pending'))
        if cursor.rowcount == 0:
            conn.close()
            return False, "Заявка не найдена"
        conn.commit()
        conn.close()
        return True, "Заявка отклонена"

    def remove_friend(self, user_id, friend_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM friends WHERE ((user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)) AND status=?',
            (user_id, friend_id, friend_id, user_id, 'accepted'))
        if cursor.rowcount == 0:
            conn.close()
            return False, "Дружба не найдена"
        cursor.execute('UPDATE users SET friends_count=MAX(0, friends_count-1) WHERE id IN (?,?)', (user_id, friend_id))
        conn.commit()
        conn.close()
        return True, "Удален из друзей"

    def get_friends(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.name, u.avatar, u.zodiac, u.status, u.city
            FROM friends f JOIN users u ON (u.id=f.friend_id OR u.id=f.user_id)
            WHERE ((f.user_id=? AND f.friend_id=u.id) OR (f.friend_id=? AND f.user_id=u.id))
            AND f.status='accepted' AND u.id!=?
        ''', (user_id, user_id, user_id))
        friends = [dict(f) for f in cursor.fetchall()]
        conn.close()
        return friends

    def get_friend_requests(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.id as request_id, u.id, u.name, u.avatar, u.zodiac, u.city, f.created_at
            FROM friends f JOIN users u ON f.user_id=u.id
            WHERE f.friend_id=? AND f.status='pending' ORDER BY f.created_at DESC
        ''', (user_id,))
        requests = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return requests

    def get_all_users(self, current_user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, name, avatar, zodiac, city, status, friends_count FROM users WHERE id!=? ORDER BY name',
            (current_user_id,))
        users = [dict(u) for u in cursor.fetchall()]
        conn.close()
        return users

    def get_friend_status(self, user_id, other_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM friends WHERE (user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)',
                       (user_id, other_id, other_id, user_id))
        rel = cursor.fetchone()
        conn.close()
        if not rel:
            return 'none'
        if rel['status'] == 'accepted':
            return 'friends'
        if rel['user_id'] == user_id:
            return 'sent'
        return 'received'


if __name__ == '__main__':
    if os.path.exists('vega.db'):
        os.remove('vega.db')
    auth = VegaAuth()
    print("\n✅ База данных создана")