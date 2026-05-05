# good.py - Система авторизации и регистрации VEGA

import sqlite3
import hashlib
import re
import os
from datetime import datetime, timedelta


class VegaAuth:
    """Класс для работы с авторизацией и регистрацией"""

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

        # Таблица пользователей
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
                status TEXT DEFAULT 'offline',
                friends_count INTEGER DEFAULT 0,
                subscribers INTEGER DEFAULT 0,
                email_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        # Таблица сессий
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

        # Таблица попыток входа
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                success INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица кодов верификации
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица постов
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

        # Таблица друзей
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

        # Таблица лайков
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

        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")

    def hash_password(self, password):
        """Хеширование пароля"""
        salt = "vega_salt_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()

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

            hashed_password = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (email, password, name, zodiac, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, hashed_password, name, zodiac, datetime.now().isoformat()))

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

        # Записываем попытку входа
        cursor.execute('''
            INSERT INTO login_attempts (email, ip_address, success, created_at)
            VALUES (?, ?, 0, ?)
        ''', (email, ip_address, datetime.now().isoformat()))

        # Проверяем количество неудачных попыток
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

        # Ищем пользователя
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user is None:
            conn.commit()
            conn.close()
            return False, "Неверный email или пароль", None

        user_dict = dict(user)

        # Проверяем пароль
        if user_dict['password'] != self.hash_password(password):
            conn.commit()
            conn.close()
            return False, "Неверный email или пароль", None

        # Успешный вход
        cursor.execute('''
            UPDATE login_attempts SET success = 1 
            WHERE email = ? AND id = (
                SELECT MAX(id) FROM login_attempts WHERE email = ?
            )
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

    def update_profile(self, user_id, data):
        """Обновление профиля"""
        allowed_fields = ['name', 'avatar', 'cover', 'bio', 'city', 'phone', 'zodiac']
        updates = {}

        for field in allowed_fields:
            if field in data and data[field]:
                updates[field] = data[field]

        if not updates:
            return False, "Нет данных для обновления"

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
            values = list(updates.values()) + [user_id]
            cursor.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
            conn.commit()
            conn.close()
            return True, "Профиль обновлен"
        except Exception as e:
            conn.close()
            return False, f"Ошибка: {str(e)}"

    def change_password(self, user_id, old_password, new_password, confirm_password):
        """Смена пароля"""
        if new_password != confirm_password:
            return False, "Новые пароли не совпадают"

        valid, msg = self.validate_password(new_password)
        if not valid:
            return False, msg

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return False, "Пользователь не найден"

        if user['password'] != self.hash_password(old_password):
            conn.close()
            return False, "Неверный текущий пароль"

        cursor.execute('UPDATE users SET password = ? WHERE id = ?',
                       (self.hash_password(new_password), user_id))
        conn.commit()
        conn.close()
        return True, "Пароль успешно изменен"

    def delete_account(self, user_id, password):
        """Удаление аккаунта"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return False, "Пользователь не найден"

        if user['password'] != self.hash_password(password):
            conn.close()
            return False, "Неверный пароль"

        cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM verification_codes WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM login_attempts WHERE email = ?', (user['email'],))
        cursor.execute('DELETE FROM posts WHERE author_id = ?', (user_id,))
        cursor.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM likes WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM friends WHERE user_id = ? OR friend_id = ?', (user_id, user_id))
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

        conn.commit()
        conn.close()
        print(f"🗑️ Аккаунт ID={user_id} удален")
        return True, "Аккаунт успешно удален"

    def get_user_stats(self, user_id):
        """Статистика пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT friends_count, subscribers FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return None

        cursor.execute('SELECT COUNT(*) as count FROM posts WHERE author_id = ?', (user_id,))
        posts = cursor.fetchone()

        cursor.execute('SELECT COUNT(*) as count FROM friends WHERE friend_id = ? AND status = ?',
                       (user_id, 'accepted'))
        friends = cursor.fetchone()

        conn.close()

        return {
            'friends_count': user['friends_count'],
            'subscribers': user['subscribers'],
            'posts_count': posts['count'] if posts else 0,
            'actual_friends': friends['count'] if friends else 0
        }

    def create_post(self, user_id, content, image=None, privacy='public'):
        """Создание поста"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (author_id, content, image, privacy)
            VALUES (?, ?, ?, ?)
        ''', (user_id, content, image, privacy))
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        return post_id

    def get_posts(self, limit=20, offset=0):
        """Получить посты"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT posts.*, users.name as author_name, users.avatar as author_avatar, users.zodiac as author_zodiac
            FROM posts 
            JOIN users ON posts.author_id = users.id 
            ORDER BY posts.created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        posts = cursor.fetchall()
        conn.close()
        return [dict(post) for post in posts]

    def get_user_posts(self, user_id, limit=10):
        """Получить посты пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM posts 
            WHERE author_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        posts = cursor.fetchall()
        conn.close()
        return [dict(post) for post in posts]

    def like_post(self, user_id, post_id):
        """Лайк поста"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM likes WHERE user_id = ? AND post_id = ?', (user_id, post_id))
        if cursor.fetchone():
            cursor.execute('DELETE FROM likes WHERE user_id = ? AND post_id = ?', (user_id, post_id))
            cursor.execute('UPDATE posts SET likes = likes - 1 WHERE id = ?', (post_id,))
            conn.commit()
            conn.close()
            return False, "Лайк удален"
        else:
            cursor.execute('INSERT INTO likes (user_id, post_id) VALUES (?, ?)', (user_id, post_id))
            cursor.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
            conn.commit()
            conn.close()
            return True, "Лайк добавлен"

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


# ======================
# ТЕСТИРОВАНИЕ
# ======================

if __name__ == '__main__':
    # Удаляем старую БД для чистого теста
    if os.path.exists('vega.db'):
        os.remove('vega.db')
        print("🗑️ Старая БД удалена")

    auth = VegaAuth()

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ VEGA")
    print("=" * 50 + "\n")

    # Тест 1: Регистрация
    print("📝 Тест 1: Регистрация")
    success, msg, user = auth.register("Максим Овчинников", "maxim@vega.ru", "pass123", "pass123", "Лев")
    print(f"{'✅' if success else '❌'} {msg}")
    if user:
        user1_id = user['id']

    success, msg, user = auth.register("Семён Трефилов", "semen@vega.ru", "pass456", "pass456", "Скорпион")
    print(f"{'✅' if success else '❌'} {msg}")
    if user:
        user2_id = user['id']

    # Тест 2: Повторная регистрация
    print("\n📝 Тест 2: Повторная регистрация")
    success, msg, _ = auth.register("Другой", "maxim@vega.ru", "pass789", "pass789")
    print(f"{'✅' if success else '❌'} {msg}")

    # Тест 3: Вход
    print("\n🔑 Тест 3: Вход")
    success, msg, user = auth.login("maxim@vega.ru", "pass123")
    print(f"{'✅' if success else '❌'} {msg}")

    # Тест 4: Неверный пароль
    print("\n🔑 Тест 4: Неверный пароль")
    success, msg, _ = auth.login("maxim@vega.ru", "wrongpass")
    print(f"{'✅' if success else '❌'} {msg}")

    # Тест 5: Создание поста
    print("\n📄 Тест 5: Создание поста")
    post_id = auth.create_post(user1_id, "Мой первый пост в VEGA! ✨")
    print(f"{'✅' if post_id else '❌'} Пост создан (ID: {post_id})")

    # Тест 6: Лайк
    print("\n❤️ Тест 6: Лайк поста")
    success, msg = auth.like_post(user2_id, post_id)
    print(f"{'✅' if success else '❌'} {msg}")

    # Тест 7: Комментарий
    print("\n💬 Тест 7: Комментарий")
    success, msg = auth.add_comment(user2_id, post_id, "Отличный пост!")
    print(f"{'✅' if success else '❌'} {msg}")

    # Тест 8: Статистика
    print("\n📊 Тест 8: Статистика")
    stats = auth.get_user_stats(user1_id)
    if stats:
        print(f"✅ Постов: {stats['posts_count']}, Друзей: {stats['actual_friends']}")

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 50)