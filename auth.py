import sqlite3
import re
import os
from datetime import datetime, timedelta


class VegaAuth:
    """Класс для работы с авторизацией и регистрацией"""

    def __init__(self, db_name='vega.db'):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE,
                email TEXT,
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
                wall_user_id INTEGER DEFAULT NULL,
                content TEXT NOT NULL,
                image TEXT,
                likes INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                is_repost INTEGER DEFAULT 0,
                original_author_id INTEGER DEFAULT NULL,
                privacy TEXT DEFAULT 'public',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users (id),
                FOREIGN KEY (wall_user_id) REFERENCES users (id),
                FOREIGN KEY (original_author_id) REFERENCES users (id)
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
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_user_id) REFERENCES users (id),
                FOREIGN KEY (to_user_id) REFERENCES users (id)
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gallery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT DEFAULT 'image',
                caption TEXT DEFAULT '',
                post_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')

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
                notifications_messages INTEGER DEFAULT 1,
                notifications_friends INTEGER DEFAULT 1,
                notifications_comments INTEGER DEFAULT 1,
                notifications_horoscope INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Добавляем недостающие колонки для старых БД
        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN wall_user_id INTEGER DEFAULT NULL")
        except: pass
        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN is_repost INTEGER DEFAULT 0")
        except: pass
        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN original_author_id INTEGER DEFAULT NULL")
        except: pass
        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN shares INTEGER DEFAULT 0")
        except: pass

        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")

    def get_user_by_id(self, user_id):
        if user_id < 0:
            return {
                'id': user_id,
                'name': f'Гость_{abs(user_id)}',
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
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def get_user_settings(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
        settings = cursor.fetchone()
        if not settings:
            cursor.execute('INSERT INTO user_settings (user_id) VALUES (?)', (user_id,))
            conn.commit()
            cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
            settings = cursor.fetchone()
        conn.close()
        return dict(settings)

    def save_user_settings(self, user_id, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_settings SET
                privacy_profile = ?, privacy_messages = ?, privacy_online = ?,
                theme = ?, font_size_px = ?, accent_color = ?,
                feed_sort = ?, posts_per_page = ?,
                notifications_messages = ?, notifications_friends = ?,
                notifications_comments = ?, notifications_horoscope = ?,
                updated_at = ?
            WHERE user_id = ?
        ''', (
            data.get('privacy_profile', 'all'),
            data.get('privacy_messages', 'all'),
            1 if data.get('privacy_online') == 'on' or data.get('privacy_online') == True else 0,
            data.get('theme', 'dark'),
            int(data.get('font_size_px', 14)),
            data.get('accent_color', '#9d7be8'),
            data.get('feed_sort', 'newest'),
            int(data.get('posts_per_page', 20)),
            1 if data.get('notifications_messages') == 'on' else 0,
            1 if data.get('notifications_friends') == 'on' else 0,
            1 if data.get('notifications_comments') == 'on' else 0,
            1 if data.get('notifications_horoscope') == 'on' else 0,
            datetime.now().isoformat(),
            user_id
        ))
        conn.commit()
        conn.close()
        return True

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

    def register(self, name, phone, password, password_confirm, zodiac='Лев'):
        name = name.strip()
        phone = phone.strip()
        if not name or not phone or not password:
            return False, "Заполните все обязательные поля", None
        valid, msg = self.validate_name(name)
        if not valid:
            return False, msg, None
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

    def guest_login(self):
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

    def login_by_phone(self, phone, password, ip_address=None):
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

    def logout(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = ? WHERE id = ?', ('offline', user_id))
        conn.commit()
        conn.close()
        return True

    def create_post(self, user_id, content, image=None, privacy='public'):
        if user_id < 0:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO posts (author_id, content, image, privacy, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, content, image, privacy, datetime.now().isoformat()))
            conn.commit()
            post_id = cursor.lastrowid
            conn.close()
            return post_id
        except Exception as e:
            print(f"Error in create_post: {e}")
            conn.close()
            return None

    def create_repost(self, user_id, original_post_id, content=''):
        """Создать репост на свою стену"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем оригинальный пост
        cursor.execute('SELECT * FROM posts WHERE id = ?', (original_post_id,))
        original_post = cursor.fetchone()
        if not original_post:
            conn.close()
            return False, "Пост не найден", None

        # Создаем пост-репост
        cursor.execute('''
            INSERT INTO posts (author_id, content, is_repost, original_author_id, created_at)
            VALUES (?, ?, 1, ?, ?)
        ''', (user_id, content, original_post['author_id'], datetime.now().isoformat()))

        conn.commit()
        post_id = cursor.lastrowid

        # Обновляем счетчик репостов в оригинальном посте
        cursor.execute('UPDATE posts SET shares = shares + 1 WHERE id = ?', (original_post_id,))
        conn.commit()

        conn.close()
        return True, "Репост создан", post_id

    def share_to_friend(self, from_user_id, to_user_id, original_post_id):
        """Отправить репост другу в личные сообщения"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем оригинальный пост и автора
        cursor.execute('''
            SELECT p.*, u.name as author_name 
            FROM posts p JOIN users u ON p.author_id = u.id 
            WHERE p.id = ?
        ''', (original_post_id,))
        post = cursor.fetchone()
        if not post:
            conn.close()
            return False, "Пост не найден"

        # Формируем сообщение с репостом
        message_text = f"📎 Поделился(лась) постом\n\n"
        message_text += f"📝 {post['content'][:200]}"
        if len(post['content']) > 200:
            message_text += "..."
        message_text += f"\n\n👤 Автор: {post['author_name']}"

        # Отправляем как личное сообщение
        cursor.execute('''
            INSERT INTO messages (from_user_id, to_user_id, message, created_at, is_read)
            VALUES (?, ?, ?, ?, 0)
        ''', (from_user_id, to_user_id, message_text, datetime.now().isoformat()))

        conn.commit()
        message_id = cursor.lastrowid

        # Обновляем счетчик репостов
        cursor.execute('UPDATE posts SET shares = shares + 1 WHERE id = ?', (original_post_id,))
        conn.commit()

        conn.close()
        return True, "Отправлено", message_id

    def get_posts(self, limit=20, offset=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                posts.*,
                users.id as author_id,
                users.name as author_name,
                users.avatar as author_avatar,
                users.zodiac as author_zodiac,
                original_author.name as original_author_name,
                original_author.avatar as original_author_avatar
            FROM posts 
            JOIN users ON posts.author_id = users.id 
            LEFT JOIN users as original_author ON posts.original_author_id = original_author.id
            WHERE users.id > 0 AND users.is_guest = 0 
            AND (posts.wall_user_id IS NULL OR posts.wall_user_id = 0 OR posts.wall_user_id = '')
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
            if post_dict.get('is_repost') and post_dict.get('original_author_name'):
                post_dict['original_author'] = {
                    'name': post_dict['original_author_name'],
                    'avatar': post_dict['original_author_avatar']
                }
            posts_list.append(post_dict)

        conn.close()
        return posts_list

    def get_user_posts(self, user_id, limit=50):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                posts.*,
                users.name as author_name,
                users.avatar as author_avatar,
                original_author.name as original_author_name,
                original_author.avatar as original_author_avatar
            FROM posts 
            JOIN users ON posts.author_id = users.id 
            LEFT JOIN users as original_author ON posts.original_author_id = original_author.id
            WHERE posts.author_id = ?
            ORDER BY posts.created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        posts = cursor.fetchall()
        posts_list = []
        for post in posts:
            post_dict = dict(post)
            if post_dict.get('is_repost') and post_dict.get('original_author_name'):
                post_dict['original_author'] = {
                    'name': post_dict['original_author_name'],
                    'avatar': post_dict['original_author_avatar']
                }
            posts_list.append(post_dict)
        conn.close()
        return posts_list

    def like_post(self, user_id, post_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM likes WHERE user_id = ? AND post_id = ?', (user_id, post_id))
        existing = cursor.fetchone()
        if existing:
            cursor.execute('DELETE FROM likes WHERE user_id = ? AND post_id = ?', (user_id, post_id))
            cursor.execute('UPDATE posts SET likes = likes - 1 WHERE id = ?', (post_id,))
            conn.commit()
            cursor.execute('SELECT likes FROM posts WHERE id = ?', (post_id,))
            result = cursor.fetchone()
            new_count = result[0] if result else 0
            conn.close()
            return True, "Лайк удален", new_count, 'unliked'
        else:
            cursor.execute('INSERT INTO likes (user_id, post_id) VALUES (?, ?)', (user_id, post_id))
            cursor.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
            conn.commit()
            cursor.execute('SELECT likes FROM posts WHERE id = ?', (post_id,))
            result = cursor.fetchone()
            new_count = result[0] if result else 0
            conn.close()
            return True, "Лайк добавлен", new_count, 'liked'

    def add_comment(self, user_id, post_id, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comments (user_id, post_id, content, created_at) VALUES (?, ?, ?, ?)',
                       (user_id, post_id, content, datetime.now().isoformat()))
        cursor.execute('UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return True, "Комментарий добавлен"

    def get_comments(self, post_id):
        conn = self.get_connection()
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
        return comments

    # Друзья
    def get_friends(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.name, u.avatar, u.zodiac, u.status, u.city
            FROM friends f JOIN users u ON (u.id = f.friend_id OR u.id = f.user_id)
            WHERE ((f.user_id = ? AND f.friend_id = u.id) OR (f.friend_id = ? AND f.user_id = u.id))
            AND f.status = 'accepted' AND u.id != ? AND u.is_guest = 0
        ''', (user_id, user_id, user_id))
        friends = [dict(f) for f in cursor.fetchall()]
        conn.close()
        return friends

    def get_friend_requests(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.id as request_id, u.id, u.name, u.avatar, u.zodiac, u.city
            FROM friends f JOIN users u ON f.user_id = u.id
            WHERE f.friend_id = ? AND f.status = 'pending' AND u.is_guest = 0
            ORDER BY f.created_at DESC
        ''', (user_id,))
        requests = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return requests

    def get_all_users(self, current_user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, avatar, zodiac, city, status, friends_count 
            FROM users WHERE id != ? AND is_guest = 0 ORDER BY name
        ''', (current_user_id,))
        users = [dict(u) for u in cursor.fetchall()]
        conn.close()
        return users

    def get_mutual_friends(self, user_id, other_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT friend_id FROM friends WHERE user_id = ? AND status = 'accepted'
            UNION SELECT user_id FROM friends WHERE friend_id = ? AND status = 'accepted'
        ''', (user_id, user_id))
        user_friends = set([row[0] for row in cursor.fetchall()])
        cursor.execute('''
            SELECT friend_id FROM friends WHERE user_id = ? AND status = 'accepted'
            UNION SELECT user_id FROM friends WHERE friend_id = ? AND status = 'accepted'
        ''', (other_id, other_id))
        other_friends = set([row[0] for row in cursor.fetchall()])
        mutual_ids = user_friends.intersection(other_friends)
        if mutual_ids:
            placeholders = ','.join('?' * len(mutual_ids))
            cursor.execute(f'''
                SELECT id, name, avatar, zodiac, status 
                FROM users WHERE id IN ({placeholders}) AND is_guest = 0 LIMIT 6
            ''', tuple(mutual_ids))
            mutual = [dict(f) for f in cursor.fetchall()]
        else:
            mutual = []
        conn.close()
        return mutual

    def get_friend_status(self, user_id, other_id):
        if user_id < 0 or other_id < 0:
            return 'none'
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

    def send_friend_request(self, user_id, friend_id):
        if user_id == friend_id:
            return False, "Нельзя добавить себя в друзья"
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, is_guest FROM users WHERE id = ?', (friend_id,))
        friend = cursor.fetchone()
        if not friend:
            conn.close()
            return False, "Пользователь не найден"
        if friend['is_guest'] == 1:
            conn.close()
            return False, "Нельзя добавить гостя в друзья"
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

    def send_message(self, from_user_id, to_user_id, message):
        if not message or not message.strip():
            return False, "Сообщение не может быть пустым", None
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (from_user_id, to_user_id, message, created_at, is_read)
            VALUES (?, ?, ?, ?, 0)
        ''', (from_user_id, to_user_id, message.strip(), datetime.now().isoformat()))
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        return True, "Сообщение отправлено", message_id

    def get_messages(self, user_id, other_user_id, limit=50):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM messages 
            WHERE (from_user_id = ? AND to_user_id = ?) 
               OR (from_user_id = ? AND to_user_id = ?)
            ORDER BY created_at ASC LIMIT ?
        ''', (user_id, other_user_id, other_user_id, user_id, limit))
        messages = [dict(m) for m in cursor.fetchall()]
        conn.close()
        self.mark_messages_as_read(user_id, other_user_id)
        return messages

    def mark_messages_as_read(self, user_id, other_user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE messages SET is_read = 1 
            WHERE from_user_id = ? AND to_user_id = ? AND is_read = 0
        ''', (other_user_id, user_id))
        conn.commit()
        conn.close()

    def get_unread_count(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM messages WHERE to_user_id = ? AND is_read = 0', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0

    def get_chat_users(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT 
                CASE WHEN from_user_id = ? THEN to_user_id ELSE from_user_id END as user_id,
                u.name, u.avatar, u.status,
                (SELECT message FROM messages 
                 WHERE (from_user_id = ? AND to_user_id = u.id) OR (from_user_id = u.id AND to_user_id = ?)
                 ORDER BY created_at DESC LIMIT 1) as last_message,
                (SELECT created_at FROM messages 
                 WHERE (from_user_id = ? AND to_user_id = u.id) OR (from_user_id = u.id AND to_user_id = ?)
                 ORDER BY created_at DESC LIMIT 1) as last_message_time,
                (SELECT COUNT(*) FROM messages 
                 WHERE from_user_id = u.id AND to_user_id = ? AND is_read = 0) as unread_count
            FROM messages m
            JOIN users u ON u.id = CASE WHEN from_user_id = ? THEN to_user_id ELSE from_user_id END
            WHERE (from_user_id = ? OR to_user_id = ?) AND u.is_guest = 0
            GROUP BY user_id
            ORDER BY last_message_time DESC
        ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
        chats = [dict(c) for c in cursor.fetchall()]
        conn.close()
        return chats

    def change_password(self, user_id, old_password, new_password, confirm_password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False, "Пользователь не найден"
        if user[0] != old_password:
            conn.close()
            return False, "Старый пароль неверен"
        if len(new_password) < 6:
            conn.close()
            return False, "Новый пароль должен содержать минимум 6 символов"
        if new_password != confirm_password:
            conn.close()
            return False, "Новые пароли не совпадают"
        cursor.execute('UPDATE users SET password = ?, updated_at = ? WHERE id = ?',
                       (new_password, datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        return True, "Пароль успешно изменен!"


if __name__ == '__main__':
    if os.path.exists('vega.db'):
        os.remove('vega.db')
    auth = VegaAuth()
    print("\n✅ База данных создана")