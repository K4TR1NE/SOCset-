import sqlite3
import re
import os
from datetime import datetime, timedelta


class VegaAuth:
    """Класс для работы с авторизацией и регистрацией"""

    def get_mutual_friends(self, user_id, other_id):
        """Получить список общих друзей"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получаем друзей первого пользователя
        cursor.execute('''
            SELECT friend_id FROM friends 
            WHERE user_id = ? AND status = 'accepted'
            UNION
            SELECT user_id FROM friends 
            WHERE friend_id = ? AND status = 'accepted'
        ''', (user_id, user_id))
        user_friends = set([row[0] for row in cursor.fetchall()])

        # Получаем друзей второго пользователя
        cursor.execute('''
            SELECT friend_id FROM friends 
            WHERE user_id = ? AND status = 'accepted'
            UNION
            SELECT user_id FROM friends 
            WHERE friend_id = ? AND status = 'accepted'
        ''', (other_id, other_id))
        other_friends = set([row[0] for row in cursor.fetchall()])

        # Находим пересечение
        mutual_ids = user_friends.intersection(other_friends)

        # Получаем данные общих друзей
        if mutual_ids:
            placeholders = ','.join('?' * len(mutual_ids))
            cursor.execute(f'''
                SELECT id, name, avatar, zodiac, status 
                FROM users WHERE id IN ({placeholders}) LIMIT 6
            ''', tuple(mutual_ids))
            mutual = [dict(f) for f in cursor.fetchall()]
        else:
            mutual = []

        conn.close()
        return mutual

    def get_comments(self, post_id):
        """Получить все комментарии к посту с информацией об авторах"""
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

    def get_comments(self, post_id):
        """Получить все комментарии к посту с информацией об авторах"""
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


    def __init__(self, db_name='vega.db'):
        """Инициализация подключения к БД"""
        self.db_name = db_name
        self.init_database()

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
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                avatar TEXT DEFAULT 'https://randomuser.me/api/portraits/men/32.jpg',
                cover TEXT DEFAULT 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d',
                zodiac TEXT DEFAULT 'Лев',
                bio TEXT DEFAULT '',
                city TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                birthday TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                website TEXT DEFAULT '',
                vk_link TEXT DEFAULT '',
                telegram_link TEXT DEFAULT '',
                status TEXT DEFAULT 'offline',
                friends_count INTEGER DEFAULT 0,
                subscribers INTEGER DEFAULT 0,
                email_verified INTEGER DEFAULT 0,
                profile_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                success INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def validate_email(self, email):
        """Валидация email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_password(self, password):
        """Проверка сложности пароля"""
        if len(password) < 6:
            return False, "Пароль должен содержать минимум 6 символов"
        if not re.search(r'[a-zA-Zа-яА-Я]', password):
            return False, "Пароль должен содержать хотя бы одну букву"
        if not re.search(r'\d', password):
            return False, "Пароль должен содержать хотя бы одну цифру"
        return True, "OK"

    def validate_name(self, name):
        """Валидация имени"""
        if len(name) < 2:
            return False, "Имя должно содержать минимум 2 символа"
        if len(name) > 50:
            return False, "Имя слишком длинное"
        return True, "OK"

    def register(self, name, email, password, password_confirm, zodiac='Лев'):
        """Регистрация нового пользователя"""
        name = name.strip()
        email = email.strip().lower()

        if not name or not email or not password:
            return False, "Заполните все обязательные поля", None

        valid, msg = self.validate_name(name)
        if not valid:
            return False, msg, None

        if not self.validate_email(email):
            return False, "Некорректный email адрес", None

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
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return False, "Пользователь с таким email уже существует", None

            # Сохраняем пароль как есть (без хэширования)
            cursor.execute('''
                INSERT INTO users (email, password, name, zodiac, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, password, name, zodiac, datetime.now().isoformat()))

            conn.commit()
            user_id = cursor.lastrowid

            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = dict(cursor.fetchone())

            conn.close()
            print(f"✅ Зарегистрирован: {name} ({email})")
            return True, "Регистрация успешна!", user

        except Exception as e:
            conn.close()
            return False, f"Ошибка при регистрации: {str(e)}", None

    def login(self, email, password, ip_address=None):
        """Вход в систему"""
        email = email.strip().lower()

        if not email or not password:
            return False, "Введите email и пароль", None

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO login_attempts (email, ip_address, success, created_at)
            VALUES (?, ?, 0, ?)
        ''', (email, ip_address, datetime.now().isoformat()))

        fifteen_min_ago = (datetime.now() - timedelta(minutes=15)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) as attempts FROM login_attempts 
            WHERE email = ? AND success = 0 AND created_at > ?
        ''', (email, fifteen_min_ago))
        result = cursor.fetchone()
        attempts = result['attempts'] if result else 0

        if attempts >= 5:
            conn.commit()
            conn.close()
            return False, "Слишком много попыток. Попробуйте через 15 минут", None

        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user is None:
            conn.commit()
            conn.close()
            return False, "Неверный email или пароль", None

        user_dict = dict(user)

        # Прямое сравнение паролей (без хэширования)
        if user_dict['password'] != password:
            conn.commit()
            conn.close()
            return False, "Неверный email или пароль", None

        cursor.execute('''
            UPDATE login_attempts SET success = 1 
            WHERE email = ? AND id = (SELECT MAX(id) FROM login_attempts WHERE email = ?)
        ''', (email, email))

        cursor.execute('UPDATE users SET last_login = ?, status = ? WHERE id = ?',
                       (datetime.now().isoformat(), 'online', user_dict['id']))
        conn.commit()
        conn.close()

        print(f"✅ Вход: {user_dict['name']} ({email})")
        return True, f"Добро пожаловать, {user_dict['name']}!", user_dict

    def logout(self, user_id):
        """Выход из системы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = ? WHERE id = ?', ('offline', user_id))
        conn.commit()
        conn.close()
        return True, "Вы вышли из системы"

    def get_user_by_id(self, user_id):
        """Получить пользователя по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def get_user_by_email(self, email):
        """Получить пользователя по email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower().strip(),))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def create_post(self, user_id, content, image=None, privacy='public'):
        """Создание поста"""
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
        """Получить все посты"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                posts.*,
                users.name as author_name,
                users.avatar as author_avatar,
                users.zodiac as author_zodiac
            FROM posts 
            JOIN users ON posts.author_id = users.id 
            ORDER BY posts.created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        posts = cursor.fetchall()

        posts_list = []
        for post in posts:
            post_dict = dict(post)
            post_dict['author'] = {
                'name': post_dict['author_name'],
                'avatar': post_dict['author_avatar'],
                'zodiac': post_dict.get('author_zodiac', 'Лев')
            }
            posts_list.append(post_dict)

        conn.close()
        return posts_list

    def get_user_posts(self, user_id, limit=10):
        """Получить посты пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM posts WHERE author_id = ? ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
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
            new_count = cursor.fetchone()[0]
            conn.close()
            return True, "Лайк удален", new_count, 'unliked'
        else:
            # Добавляем лайк
            cursor.execute('INSERT INTO likes (user_id, post_id) VALUES (?, ?)', (user_id, post_id))
            cursor.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
            conn.commit()

            # Получаем новое количество лайков
            cursor.execute('SELECT likes FROM posts WHERE id = ?', (post_id,))
            new_count = cursor.fetchone()[0]
            conn.close()
            return True, "Лайк добавлен", new_count, 'liked'

    def add_comment(self, user_id, post_id, content):
        """Добавить комментарий"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO comments (user_id, post_id, content) VALUES (?, ?, ?)',
                       (user_id, post_id, content))
        cursor.execute('UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        return True, "Комментарий добавлен"

    # Методы для друзей
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
        if not rel: return 'none'
        if rel['status'] == 'accepted': return 'friends'
        if rel['user_id'] == user_id: return 'sent'
        return 'received'


if __name__ == '__main__':
    if os.path.exists('vega.db'):
        os.remove('vega.db')
    auth = VegaAuth()
    print("\n✅ База данных создана")
    success, msg, user = auth.register("Тест", "test@test.ru", "pass123", "pass123", "Лев")
    if success:
        print(f"✅ Тестовый пользователь создан (ID: {user['id']})")
        print(f"✅ Пароль в БД: {user['password']}")  # Будет видно что пароль сохранился как "pass123"
        post_id = auth.create_post(user['id'], "Тестовый пост!")
        print(f"✅ Тестовый пост создан (ID: {post_id})")