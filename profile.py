# profile.py - Система управления профилем VEGA

import sqlite3
from datetime import datetime, timedelta


class VegaProfile:
    """Класс для работы с профилем пользователя"""

    def __init__(self, db_name='vega.db'):
        """Инициализация подключения к БД"""
        self.db_name = db_name
        self.init_profile_tables()

    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_profile_tables(self):
        """Создание таблиц для профиля"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Обновляем таблицу users - добавляем новые поля
        cursor.executescript('''
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
            );

            CREATE TABLE IF NOT EXISTS user_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                photo_url TEXT NOT NULL,
                description TEXT DEFAULT '',
                is_avatar INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS user_hobbies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                hobby TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        ''')

        conn.commit()
        conn.close()
        print("✅ Таблицы профиля инициализированы")

    def get_profile(self, user_id):
        """Получить полный профиль пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Основная информация
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return None

        user_dict = dict(user)

        # Фотографии
        cursor.execute('SELECT * FROM user_photos WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        user_dict['photos'] = [dict(p) for p in cursor.fetchall()]

        # Хобби
        cursor.execute('SELECT * FROM user_hobbies WHERE user_id = ?', (user_id,))
        user_dict['hobbies'] = [dict(h)['hobby'] for h in cursor.fetchall()]

        # Статистика постов
        cursor.execute('SELECT COUNT(*) as count FROM posts WHERE author_id = ?', (user_id,))
        user_dict['posts_count'] = cursor.fetchone()['count']

        # Статистика друзей
        cursor.execute('SELECT COUNT(*) as count FROM friends WHERE (user_id = ? OR friend_id = ?) AND status = ?',
                       (user_id, user_id, 'accepted'))
        user_dict['actual_friends'] = cursor.fetchone()['count']

        conn.close()
        return user_dict

    def update_profile(self, user_id, data):
        """
        Обновление профиля пользователя
        data - словарь с полями для обновления
        """
        allowed_fields = [
            'name', 'avatar', 'cover', 'zodiac', 'bio', 'city',
            'phone', 'birthday', 'gender', 'website', 'vk_link',
            'telegram_link', 'status'
        ]

        updates = {}
        for field in allowed_fields:
            if field in data and data[field] is not None:
                updates[field] = data[field].strip() if isinstance(data[field], str) else data[field]

        if not updates:
            return False, "Нет данных для обновления"

        # Проверка имени
        if 'name' in updates:
            if len(updates['name']) < 2:
                return False, "Имя должно содержать минимум 2 символа"
            if len(updates['name']) > 50:
                return False, "Имя слишком длинное"

        # Проверка знака зодиака
        if 'zodiac' in updates:
            valid_zodiacs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
                             'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
            if updates['zodiac'] not in valid_zodiacs:
                return False, "Некорректный знак зодиака"

        # Проверка телефона
        if 'phone' in updates and updates['phone']:
            import re
            if not re.match(r'^[\d\+\-\(\)\s]+$', updates['phone']):
                return False, "Некорректный формат телефона"

        # Добавляем дату обновления
        updates['updated_at'] = datetime.now().isoformat()

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
            values = list(updates.values()) + [user_id]

            cursor.execute(f'UPDATE users SET {set_clause}, profile_completed = 1 WHERE id = ?', values)
            conn.commit()
            conn.close()

            return True, "Профиль успешно обновлен"

        except Exception as e:
            conn.close()
            return False, f"Ошибка обновления: {str(e)}"

    def update_avatar(self, user_id, avatar_url):
        """Обновление аватара"""
        if not avatar_url or not avatar_url.strip():
            return False, "URL аватара не может быть пустым"

        avatar_url = avatar_url.strip()

        # Проверяем, что это похоже на URL
        if not (avatar_url.startswith('http://') or avatar_url.startswith('https://')):
            return False, "Некорректный URL"

        return self.update_profile(user_id, {'avatar': avatar_url})

    def update_cover(self, user_id, cover_url):
        """Обновление обложки"""
        if not cover_url or not cover_url.strip():
            return False, "URL обложки не может быть пустым"

        return self.update_profile(user_id, {'cover': cover_url.strip()})

    def add_photo(self, user_id, photo_url, description=''):
        """Добавить фотографию"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Считаем количество фото
        cursor.execute('SELECT COUNT(*) as count FROM user_photos WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()['count']

        if count >= 20:
            conn.close()
            return False, "Максимальное количество фото: 20"

        cursor.execute('''
            INSERT INTO user_photos (user_id, photo_url, description)
            VALUES (?, ?, ?)
        ''', (user_id, photo_url, description))

        conn.commit()
        photo_id = cursor.lastrowid
        conn.close()

        return True, "Фото добавлено", photo_id

    def delete_photo(self, photo_id, user_id):
        """Удалить фотографию"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM user_photos WHERE id = ? AND user_id = ?', (photo_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "Фото не найдено"

        conn.commit()
        conn.close()
        return True, "Фото удалено"

    def add_hobby(self, user_id, hobby):
        """Добавить хобби"""
        hobby = hobby.strip()
        if not hobby:
            return False, "Хобби не может быть пустым"

        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем, нет ли уже такого хобби
        cursor.execute('SELECT id FROM user_hobbies WHERE user_id = ? AND hobby = ?', (user_id, hobby))
        if cursor.fetchone():
            conn.close()
            return False, "Такое хобби уже добавлено"

        # Максимум 10 хобби
        cursor.execute('SELECT COUNT(*) as count FROM user_hobbies WHERE user_id = ?', (user_id,))
        if cursor.fetchone()['count'] >= 10:
            conn.close()
            return False, "Максимальное количество хобби: 10"

        cursor.execute('INSERT INTO user_hobbies (user_id, hobby) VALUES (?, ?)', (user_id, hobby))
        conn.commit()
        conn.close()

        return True, "Хобби добавлено"

    def remove_hobby(self, hobby_id, user_id):
        """Удалить хобби"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_hobbies WHERE id = ? AND user_id = ?', (hobby_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "Хобби не найдено"

        conn.commit()
        conn.close()
        return True, "Хобби удалено"

    def get_user_stats(self, user_id):
        """Получить статистику пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                friends_count,
                subscribers,
                (SELECT COUNT(*) FROM posts WHERE author_id = ?) as posts_count,
                (SELECT COUNT(*) FROM user_photos WHERE user_id = ?) as photos_count,
                (SELECT COUNT(*) FROM user_hobbies WHERE user_id = ?) as hobbies_count,
                created_at,
                last_login
            FROM users WHERE id = ?
        ''', (user_id, user_id, user_id, user_id))

        stats = cursor.fetchone()
        conn.close()

        if stats:
            return dict(stats)
        return None

    def search_users(self, query, limit=20):
        """Поиск пользователей по имени или городу"""
        conn = self.get_connection()
        cursor = conn.cursor()

        search = f'%{query}%'
        cursor.execute('''
            SELECT id, name, avatar, zodiac, city, status
            FROM users 
            WHERE name LIKE ? OR city LIKE ?
            LIMIT ?
        ''', (search, search, limit))

        users = [dict(u) for u in cursor.fetchall()]
        conn.close()
        return users

    def get_zodiac_info(self, zodiac_sign):
        """Получить информацию о знаке зодиака"""
        zodiac_data = {
            'Овен': {
                'emoji': '♈', 'element': 'Огонь', 'planet': 'Марс',
                'date_range': '21.03 - 19.04',
                'description': 'Овны - энергичные и целеустремленные лидеры.',
                'strengths': 'Решительность, смелость, энтузиазм',
                'weaknesses': 'Импульсивность, нетерпеливость',
                'lucky_numbers': [1, 9, 17, 25, 33],
                'lucky_color': 'Красный',
                'compatibility': ['Лев', 'Стрелец', 'Близнецы']
            },
            'Телец': {
                'emoji': '♉', 'element': 'Земля', 'planet': 'Венера',
                'date_range': '20.04 - 20.05',
                'description': 'Тельцы - надежные и практичные люди.',
                'strengths': 'Надежность, терпение, практичность',
                'weaknesses': 'Упрямство, консерватизм',
                'lucky_numbers': [2, 6, 14, 22, 30],
                'lucky_color': 'Зеленый',
                'compatibility': ['Дева', 'Козерог', 'Рак']
            },
            'Близнецы': {
                'emoji': '♊', 'element': 'Воздух', 'planet': 'Меркурий',
                'date_range': '21.05 - 20.06',
                'description': 'Близнецы - общительные и любознательные.',
                'strengths': 'Коммуникабельность, адаптивность',
                'weaknesses': 'Непостоянство, поверхностность',
                'lucky_numbers': [3, 5, 12, 21, 30],
                'lucky_color': 'Желтый',
                'compatibility': ['Весы', 'Водолей', 'Лев']
            },
            'Рак': {
                'emoji': '♋', 'element': 'Вода', 'planet': 'Луна',
                'date_range': '21.06 - 22.07',
                'description': 'Раки - эмоциональные и заботливые.',
                'strengths': 'Эмпатия, преданность, интуиция',
                'weaknesses': 'Эмоциональность, обидчивость',
                'lucky_numbers': [4, 7, 11, 19, 26],
                'lucky_color': 'Серебряный',
                'compatibility': ['Скорпион', 'Рыбы', 'Телец']
            },
            'Лев': {
                'emoji': '♌', 'element': 'Огонь', 'planet': 'Солнце',
                'date_range': '23.07 - 22.08',
                'description': 'Львы - харизматичные и творческие лидеры.',
                'strengths': 'Уверенность, щедрость, креативность',
                'weaknesses': 'Гордыня, тщеславие',
                'lucky_numbers': [1, 8, 15, 23, 42],
                'lucky_color': 'Золотой',
                'compatibility': ['Овен', 'Стрелец', 'Близнецы']
            },
            'Дева': {
                'emoji': '♍', 'element': 'Земля', 'planet': 'Меркурий',
                'date_range': '23.08 - 22.09',
                'description': 'Девы - аналитичные и трудолюбивые.',
                'strengths': 'Внимательность, практичность, ум',
                'weaknesses': 'Критичность, перфекционизм',
                'lucky_numbers': [5, 14, 23, 32, 41],
                'lucky_color': 'Коричневый',
                'compatibility': ['Телец', 'Козерог', 'Рак']
            },
            'Весы': {
                'emoji': '♎', 'element': 'Воздух', 'planet': 'Венера',
                'date_range': '23.09 - 22.10',
                'description': 'Весы - дипломатичные и гармоничные.',
                'strengths': 'Дипломатичность, справедливость',
                'weaknesses': 'Нерешительность',
                'lucky_numbers': [2, 6, 9, 15, 24],
                'lucky_color': 'Розовый',
                'compatibility': ['Близнецы', 'Водолей', 'Лев']
            },
            'Скорпион': {
                'emoji': '♏', 'element': 'Вода', 'planet': 'Плутон',
                'date_range': '23.10 - 21.11',
                'description': 'Скорпионы - страстные и решительные.',
                'strengths': 'Решительность, храбрость, верность',
                'weaknesses': 'Ревность, скрытность',
                'lucky_numbers': [4, 8, 11, 19, 27],
                'lucky_color': 'Бордовый',
                'compatibility': ['Рак', 'Рыбы', 'Дева']
            },
            'Стрелец': {
                'emoji': '♐', 'element': 'Огонь', 'planet': 'Юпитер',
                'date_range': '22.11 - 21.12',
                'description': 'Стрельцы - оптимистичные и свободолюбивые.',
                'strengths': 'Оптимизм, честность, любознательность',
                'weaknesses': 'Бестактность, нетерпеливость',
                'lucky_numbers': [3, 7, 9, 18, 27],
                'lucky_color': 'Фиолетовый',
                'compatibility': ['Овен', 'Лев', 'Водолей']
            },
            'Козерог': {
                'emoji': '♑', 'element': 'Земля', 'planet': 'Сатурн',
                'date_range': '22.12 - 19.01',
                'description': 'Козероги - дисциплинированные и амбициозные.',
                'strengths': 'Дисциплина, ответственность',
                'weaknesses': 'Пессимизм, упрямство',
                'lucky_numbers': [1, 4, 8, 10, 13],
                'lucky_color': 'Черный',
                'compatibility': ['Телец', 'Дева', 'Скорпион']
            },
            'Водолей': {
                'emoji': '♒', 'element': 'Воздух', 'planet': 'Уран',
                'date_range': '20.01 - 18.02',
                'description': 'Водолеи - независимые и изобретательные.',
                'strengths': 'Оригинальность, независимость',
                'weaknesses': 'Непредсказуемость, отстраненность',
                'lucky_numbers': [2, 7, 11, 16, 23],
                'lucky_color': 'Синий',
                'compatibility': ['Близнецы', 'Весы', 'Стрелец']
            },
            'Рыбы': {
                'emoji': '♓', 'element': 'Вода', 'planet': 'Нептун',
                'date_range': '19.02 - 20.03',
                'description': 'Рыбы - мечтательные и интуитивные.',
                'strengths': 'Интуиция, сострадание, креативность',
                'weaknesses': 'Эскапизм, нерешительность',
                'lucky_numbers': [3, 7, 12, 16, 21],
                'lucky_color': 'Бирюзовый',
                'compatibility': ['Рак', 'Скорпион', 'Телец']
            }
        }

        return zodiac_data.get(zodiac_sign, zodiac_data['Лев'])

    def generate_horoscope(self, zodiac_sign):
        """Генерация гороскопа"""
        import random

        today_predictions = [
            "Отличный день для новых начинаний и творческих проектов.",
            "Звезды советуют быть осторожнее в финансовых вопросах.",
            "День благоприятен для общения и новых знакомств.",
            "Прислушайтесь к своей интуиции - она подскажет верный путь.",
            "Хороший день для завершения старых дел и планирования новых.",
            "Возможны неожиданные встречи, которые изменят ваши планы.",
            "Энергия дня способствует активным действиям и достижениям."
        ]

        love_predictions = [
            "В личной жизни наступает гармоничный период.",
            "Одиноких представителей знака ждет интересное знакомство.",
            "Уделите больше внимания своему партнеру.",
            "Романтический вечер будет особенно удачным.",
            "Не бойтесь выражать свои чувства открыто."
        ]

        career_predictions = [
            "На работе вас ждет признание и успех.",
            "Ваши идеи будут услышаны руководством.",
            "Возможно повышение или интересное предложение.",
            "Сосредоточьтесь на важных задачах - результат не заставит ждать.",
            "Хороший день для деловых переговоров и заключения сделок."
        ]

        zodiac_info = self.get_zodiac_info(zodiac_sign)

        return {
            'name': zodiac_sign,
            'emoji': zodiac_info['emoji'],
            'element': zodiac_info['element'],
            'planet': zodiac_info['planet'],
            'date_range': zodiac_info['date_range'],
            'description': zodiac_info['description'],
            'today': random.choice(today_predictions),
            'love': random.choice(love_predictions),
            'career': random.choice(career_predictions),
            'lucky_numbers': zodiac_info['lucky_numbers'],
            'lucky_color': zodiac_info['lucky_color'],
            'compatibility': zodiac_info['compatibility']
        }

    def complete_profile_percentage(self, user_id):
        """Процент заполнения профиля"""
        profile = self.get_profile(user_id)
        if not profile:
            return 0

        fields = ['name', 'email', 'zodiac', 'city', 'phone', 'bio', 'birthday', 'avatar', 'website']
        filled = sum(1 for field in fields if profile.get(field))

        return int((filled / len(fields)) * 100)


# ======================
# ТЕСТИРОВАНИЕ
# ======================

if __name__ == '__main__':
    import os

    if os.path.exists('vega.db'):
        os.remove('vega.db')
        print("🗑️ Старая БД удалена")

    profile_manager = VegaProfile()

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ ПРОФИЛЕЙ VEGA")
    print("=" * 50 + "\n")

    # Создаем тестового пользователя через auth
    from good import VegaAuth

    auth = VegaAuth()

    success, msg, user = auth.register("Тестовый Пользователь", "test@vega.ru", "pass123", "pass123", "Лев")
    if success:
        user_id = user['id']
        print(f"✅ Пользователь создан (ID: {user_id})")

        # Тест 1: Получение профиля
        print("\n📋 Тест 1: Получение профиля")
        profile = profile_manager.get_profile(user_id)
        print(f"✅ Имя: {profile['name']}, Знак: {profile['zodiac']}")

        # Тест 2: Обновление профиля
        print("\n✏️ Тест 2: Обновление профиля")
        success, msg = profile_manager.update_profile(user_id, {
            'city': 'Ижевск',
            'phone': '+7 (999) 123-45-67',
            'bio': 'Люблю астрологию и программирование',
            'birthday': '2000-01-01'
        })
        print(f"{'✅' if success else '❌'} {msg}")

        # Тест 3: Добавление хобби
        print("\n🎯 Тест 3: Добавление хобби")
        hobbies = ['Астрология', 'Программирование', 'Музыка', 'Фотография']
        for hobby in hobbies:
            success, msg = profile_manager.add_hobby(user_id, hobby)
            print(f"  {'✅' if success else '❌'} {hobby}: {msg}")

        # Тест 4: Статистика
        print("\n📊 Тест 4: Статистика")
        stats = profile_manager.get_user_stats(user_id)
        print(f"✅ Постов: {stats['posts_count']}, Фото: {stats['photos_count']}, Хобби: {stats['hobbies_count']}")

        # Тест 5: Процент заполнения
        print("\n📈 Тест 5: Процент заполнения профиля")
        percentage = profile_manager.complete_profile_percentage(user_id)
        print(f"✅ Профиль заполнен на {percentage}%")

        # Тест 6: Гороскоп
        print("\n🌟 Тест 6: Генерация гороскопа")
        horoscope = profile_manager.generate_horoscope('Лев')
        print(f"✅ {horoscope['emoji']} {horoscope['name']}: {horoscope['today'][:50]}...")

        # Тест 7: Информация о знаке
        print("\n🔮 Тест 7: Информация о знаке")
        zodiac_info = profile_manager.get_zodiac_info('Скорпион')
        print(f"✅ Скорпион: {zodiac_info['element']}, {zodiac_info['planet']}, {zodiac_info['strengths']}")

        # Тест 8: Поиск пользователей
        print("\n🔍 Тест 8: Поиск пользователей")
        users = profile_manager.search_users('Тест')
        print(f"✅ Найдено пользователей: {len(users)}")

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 50)