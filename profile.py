import sqlite3
from datetime import datetime, timedelta
import random
import re


class VegaProfile:
    """Класс для работы с профилем пользователя"""

    def __init__(self, db_name='vega.db'):
        """Инициализация подключения к БД"""
        self.db_name = db_name
        self.init_profile_tables()
        self.init_profile_tables_with_history()

    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_profile_tables(self):
        """Создание таблиц для профиля"""
        conn = self.get_connection()
        cursor = conn.cursor()

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

    def init_profile_tables_with_history(self):
        """Расширенная инициализация таблиц (история + подсказки)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profile_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profile_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                suggestion_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                action_url TEXT,
                is_dismissed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Расширенные таблицы (история + подсказки) созданы")

    def get_profile(self, user_id):
        """Получить полный профиль пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return None

        user_dict = dict(user)

        cursor.execute('SELECT * FROM user_photos WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        user_dict['photos'] = [dict(p) for p in cursor.fetchall()]

        cursor.execute('SELECT * FROM user_hobbies WHERE user_id = ?', (user_id,))
        user_dict['hobbies'] = [dict(h)['hobby'] for h in cursor.fetchall()]

        cursor.execute('SELECT COUNT(*) as count FROM posts WHERE author_id = ?', (user_id,))
        result = cursor.fetchone()
        user_dict['posts_count'] = result['count'] if result else 0

        conn.close()
        return user_dict

    def update_profile(self, user_id, data):
        """Обновление профиля пользователя"""
        allowed_fields = [
            'name', 'avatar', 'cover', 'zodiac', 'bio', 'city',
            'phone', 'birthday', 'gender', 'website', 'vk_link',
            'telegram_link', 'status'
        ]

        old_profile = self.get_profile(user_id)

        updates = {}
        for field in allowed_fields:
            if field in data and data[field] is not None:
                updates[field] = data[field].strip() if isinstance(data[field], str) else data[field]

        if not updates:
            return False, "Нет данных для обновления"

        if 'name' in updates:
            if len(updates['name']) < 2:
                return False, "Имя должно содержать минимум 2 символа"
            if len(updates['name']) > 50:
                return False, "Имя слишком длинное"

        if 'zodiac' in updates:
            valid_zodiacs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
                             'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
            if updates['zodiac'] not in valid_zodiacs:
                return False, "Некорректный знак зодиака"

        if 'phone' in updates and updates['phone']:
            if not re.match(r'^[\d\+\-\(\)\s]+$', updates['phone']):
                return False, "Некорректный формат телефона"

        updates['updated_at'] = datetime.now().isoformat()

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
            values = list(updates.values()) + [user_id]

            cursor.execute(f'UPDATE users SET {set_clause}, profile_completed = 1 WHERE id = ?', values)
            conn.commit()

            if old_profile:
                for key, new_value in updates.items():
                    if key != 'updated_at':
                        old_value = old_profile.get(key, '')
                        if str(old_value) != str(new_value):
                            self.log_change(user_id, key, old_value, new_value)

            self.generate_and_store_suggestions(user_id)

            conn.close()
            return True, "Профиль успешно обновлен"

        except Exception as e:
            conn.close()
            return False, f"Ошибка обновления: {str(e)}"

    def log_change(self, user_id, field_name, old_value, new_value):
        """Записать изменение в историю"""
        if str(old_value) == str(new_value):
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO profile_history (user_id, field_name, old_value, new_value)
            VALUES (?, ?, ?, ?)
        ''', (user_id, field_name, str(old_value) if old_value else '', str(new_value) if new_value else ''))
        conn.commit()
        conn.close()

    def get_profile_history(self, user_id, limit=20):
        """Получить историю изменений профиля"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT field_name, old_value, new_value, changed_at
            FROM profile_history
            WHERE user_id = ?
            ORDER BY changed_at DESC
            LIMIT ?
        ''', (user_id, limit))
        history = [dict(h) for h in cursor.fetchall()]
        conn.close()
        return history

    def generate_suggestions(self, user_id):
        """Сгенерировать персонализированные подсказки"""
        profile = self.get_profile(user_id)
        if not profile:
            return []

        suggestions = []

        empty_fields = []
        for field in ['bio', 'city', 'phone', 'birthday', 'website']:
            if not profile.get(field):
                empty_fields.append(field)

        if empty_fields:
            field_names = {
                'bio': '📝 расскажите о себе',
                'city': '📍 укажите город',
                'phone': '📞 добавьте телефон',
                'birthday': '🎂 укажите дату рождения',
                'website': '🌐 добавьте сайт'
            }
            suggestions.append({
                'type': 'profile_completion',
                'title': 'Заполните профиль полностью',
                'message': f'Осталось заполнить: {", ".join([field_names[f] for f in empty_fields])}',
                'priority': 'high'
            })

        if len(profile.get('photos', [])) < 3:
            suggestions.append({
                'type': 'add_photos',
                'title': 'Добавьте больше фото',
                'message': 'У вас всего несколько фото. Добавьте ещё 2-3, чтобы профиль выглядел живее.',
                'priority': 'medium'
            })

        if len(profile.get('hobbies', [])) < 3:
            suggestions.append({
                'type': 'add_hobbies',
                'title': 'Расскажите о хобби',
                'message': 'Хобби помогают найти единомышленников. Добавьте хотя бы 3!',
                'priority': 'medium'
            })

        return suggestions

    def generate_and_store_suggestions(self, user_id):
        """Сгенерировать и сохранить подсказки в БД"""
        suggestions = self.generate_suggestions(user_id)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM profile_suggestions WHERE user_id = ? AND is_dismissed = 0', (user_id,))

        for s in suggestions[:5]:
            cursor.execute('''
                INSERT INTO profile_suggestions (user_id, suggestion_type, title, message, action_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, s['type'], s['title'], s['message'], s.get('action_url', '')))

        conn.commit()
        conn.close()

    def get_active_suggestions(self, user_id):
        """Получить активные (не отклонённые) подсказки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, suggestion_type, title, message, action_url, created_at
            FROM profile_suggestions
            WHERE user_id = ? AND is_dismissed = 0
            ORDER BY created_at DESC
        ''', (user_id,))
        suggestions = [dict(s) for s in cursor.fetchall()]
        conn.close()
        return suggestions

    def dismiss_suggestion(self, suggestion_id, user_id):
        """Отклонить подсказку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE profile_suggestions 
            SET is_dismissed = 1 
            WHERE id = ? AND user_id = ?
        ''', (suggestion_id, user_id))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def get_profile_activity_feed(self, user_id, limit=30):
        """Лента активности профиля"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                'change' as type,
                field_name as action,
                old_value || ' → ' || new_value as description,
                changed_at as created_at
            FROM profile_history
            WHERE user_id = ?

            UNION ALL

            SELECT 
                'hobby' as type,
                'Добавлено хобби' as action,
                hobby as description,
                created_at
            FROM user_hobbies
            WHERE user_id = ?

            UNION ALL

            SELECT 
                'photo' as type,
                'Новое фото' as action,
                photo_url as description,
                created_at
            FROM user_photos
            WHERE user_id = ?

            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, user_id, user_id, limit))

        feed = [dict(f) for f in cursor.fetchall()]
        conn.close()
        return feed

    def get_profile_with_meta(self, user_id):
        """Получить профиль + историю + подсказки + прогресс"""
        profile = self.get_profile(user_id)
        if not profile:
            return None

        profile['completion_percentage'] = self.complete_profile_percentage(user_id)
        profile['recent_history'] = self.get_profile_history(user_id, limit=10)
        profile['suggestions'] = self.get_active_suggestions(user_id)
        profile['recent_activity'] = self.get_profile_activity_feed(user_id, limit=15)

        empty_fields = []
        required_fields = ['bio', 'city', 'phone', 'birthday', 'website']
        for field in required_fields:
            if not profile.get(field):
                empty_fields.append(field)
        profile['empty_fields'] = empty_fields

        return profile

    def update_avatar(self, user_id, avatar_url):
        """Обновление аватара"""
        if not avatar_url or not avatar_url.strip():
            return False, "URL аватара не может быть пустым"

        avatar_url = avatar_url.strip()

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

        self.generate_and_store_suggestions(user_id)

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

        cursor.execute('SELECT id FROM user_hobbies WHERE user_id = ? AND hobby = ?', (user_id, hobby))
        if cursor.fetchone():
            conn.close()
            return False, "Такое хобби уже добавлено"

        cursor.execute('SELECT COUNT(*) as count FROM user_hobbies WHERE user_id = ?', (user_id,))
        if cursor.fetchone()['count'] >= 10:
            conn.close()
            return False, "Максимальное количество хобби: 10"

        cursor.execute('INSERT INTO user_hobbies (user_id, hobby) VALUES (?, ?)', (user_id, hobby))
        conn.commit()
        conn.close()

        self.generate_and_store_suggestions(user_id)

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
                'description': 'Овны - энергичные и целеустремленные лидеры. Они всегда идут вперед и не боятся трудностей.',
                'strengths': 'Решительность, смелость, энтузиазм, оптимизм',
                'weaknesses': 'Импульсивность, нетерпеливость, вспыльчивость',
                'lucky_numbers': [1, 9, 17, 25, 33],
                'lucky_color': 'Красный',
                'compatibility': ['Лев', 'Стрелец', 'Близнецы']
            },
            'Телец': {
                'emoji': '♉', 'element': 'Земля', 'planet': 'Венера',
                'date_range': '20.04 - 20.05',
                'description': 'Тельцы - надежные и практичные люди. Они ценят комфорт и стабильность во всем.',
                'strengths': 'Надежность, терпение, практичность, верность',
                'weaknesses': 'Упрямство, консерватизм, медлительность',
                'lucky_numbers': [2, 6, 14, 22, 30],
                'lucky_color': 'Зеленый',
                'compatibility': ['Дева', 'Козерог', 'Рак']
            },
            'Близнецы': {
                'emoji': '♊', 'element': 'Воздух', 'planet': 'Меркурий',
                'date_range': '21.05 - 20.06',
                'description': 'Близнецы - общительные и любознательные. Они легко адаптируются к любым изменениям.',
                'strengths': 'Коммуникабельность, адаптивность, остроумие',
                'weaknesses': 'Непостоянство, поверхностность, болтливость',
                'lucky_numbers': [3, 5, 12, 21, 30],
                'lucky_color': 'Желтый',
                'compatibility': ['Весы', 'Водолей', 'Лев']
            },
            'Рак': {
                'emoji': '♋', 'element': 'Вода', 'planet': 'Луна',
                'date_range': '21.06 - 22.07',
                'description': 'Раки - эмоциональные и заботливые. Семья для них самое важное в жизни.',
                'strengths': 'Эмпатия, преданность, интуиция, заботливость',
                'weaknesses': 'Эмоциональность, обидчивость, мнительность',
                'lucky_numbers': [4, 7, 11, 19, 26],
                'lucky_color': 'Серебряный',
                'compatibility': ['Скорпион', 'Рыбы', 'Телец']
            },
            'Лев': {
                'emoji': '♌', 'element': 'Огонь', 'planet': 'Солнце',
                'date_range': '23.07 - 22.08',
                'description': 'Львы - харизматичные и творческие лидеры. Они любят быть в центре внимания.',
                'strengths': 'Уверенность, щедрость, креативность, благородство',
                'weaknesses': 'Гордыня, тщеславие, властность',
                'lucky_numbers': [1, 8, 15, 23, 42],
                'lucky_color': 'Золотой',
                'compatibility': ['Овен', 'Стрелец', 'Близнецы']
            },
            'Дева': {
                'emoji': '♍', 'element': 'Земля', 'planet': 'Меркурий',
                'date_range': '23.08 - 22.09',
                'description': 'Девы - аналитичные и трудолюбивые. Они стремятся к совершенству во всем.',
                'strengths': 'Внимательность, практичность, ум, организованность',
                'weaknesses': 'Критичность, перфекционизм, придирчивость',
                'lucky_numbers': [5, 14, 23, 32, 41],
                'lucky_color': 'Коричневый',
                'compatibility': ['Телец', 'Козерог', 'Рак']
            },
            'Весы': {
                'emoji': '♎', 'element': 'Воздух', 'planet': 'Венера',
                'date_range': '23.09 - 22.10',
                'description': 'Весы - дипломатичные и гармоничные. Они всегда ищут баланс во всем.',
                'strengths': 'Дипломатичность, справедливость, обаяние, тактичность',
                'weaknesses': 'Нерешительность, зависимость от мнения других',
                'lucky_numbers': [2, 6, 9, 15, 24],
                'lucky_color': 'Розовый',
                'compatibility': ['Близнецы', 'Водолей', 'Лев']
            },
            'Скорпион': {
                'emoji': '♏', 'element': 'Вода', 'planet': 'Плутон',
                'date_range': '23.10 - 21.11',
                'description': 'Скорпионы - страстные и решительные. Они добиваются своих целей любой ценой.',
                'strengths': 'Решительность, храбрость, верность, страстность',
                'weaknesses': 'Ревность, скрытность, мстительность',
                'lucky_numbers': [4, 8, 11, 19, 27],
                'lucky_color': 'Бордовый',
                'compatibility': ['Рак', 'Рыбы', 'Дева']
            },
            'Стрелец': {
                'emoji': '♐', 'element': 'Огонь', 'planet': 'Юпитер',
                'date_range': '22.11 - 21.12',
                'description': 'Стрельцы - оптимистичные и свободолюбивые. Они любят путешествовать и узнавать новое.',
                'strengths': 'Оптимизм, честность, любознательность, щедрость',
                'weaknesses': 'Бестактность, нетерпеливость, прямолинейность',
                'lucky_numbers': [3, 7, 9, 18, 27],
                'lucky_color': 'Фиолетовый',
                'compatibility': ['Овен', 'Лев', 'Водолей']
            },
            'Козерог': {
                'emoji': '♑', 'element': 'Земля', 'planet': 'Сатурн',
                'date_range': '22.12 - 19.01',
                'description': 'Козероги - дисциплинированные и амбициозные. Они всегда добиваются поставленных целей.',
                'strengths': 'Дисциплина, ответственность, терпение, амбициозность',
                'weaknesses': 'Пессимизм, упрямство, замкнутость',
                'lucky_numbers': [1, 4, 8, 10, 13],
                'lucky_color': 'Черный',
                'compatibility': ['Телец', 'Дева', 'Скорпион']
            },
            'Водолей': {
                'emoji': '♒', 'element': 'Воздух', 'planet': 'Уран',
                'date_range': '20.01 - 18.02',
                'description': 'Водолеи - независимые и изобретательные. Они всегда придумывают что-то новое.',
                'strengths': 'Оригинальность, независимость, дружелюбие, интеллект',
                'weaknesses': 'Непредсказуемость, отстраненность, эксцентричность',
                'lucky_numbers': [2, 7, 11, 16, 23],
                'lucky_color': 'Синий',
                'compatibility': ['Близнецы', 'Весы', 'Стрелец']
            },
            'Рыбы': {
                'emoji': '♓', 'element': 'Вода', 'planet': 'Нептун',
                'date_range': '19.02 - 20.03',
                'description': 'Рыбы - мечтательные и интуитивные. Они очень чувствительны и творческие.',
                'strengths': 'Интуиция, сострадание, креативность, доброта',
                'weaknesses': 'Эскапизм, нерешительность, ранимость',
                'lucky_numbers': [3, 7, 12, 16, 21],
                'lucky_color': 'Бирюзовый',
                'compatibility': ['Рак', 'Скорпион', 'Телец']
            }
        }
        return zodiac_data.get(zodiac_sign, zodiac_data['Лев'])

    def get_daily_horoscope(self, zodiac_sign):
        """Возвращает гороскоп на сегодня для указанного знака (данные с mirkosmosa.ru)"""

        # Данные гороскопа на 25 мая 2026 с сайта mirkosmosa.ru
        horoscope_data = {
            'Овен': {
                'today': 'Овны, ваши достижения сегодня будут зависеть от вашего утреннего настроения. Внутренняя энергия у вас есть, но её направление зависит от вас. Если вы на позитиве, то сможете творить чудеса!',
                'love': '❤️ 21%',
                'relationships': '👩❤️💋👨 58%',
                'marriage': '💍 77%',
                'friendship': '🤝 68%',
                'work': '💼 57%',
                'health': '💪 56%',
                'advice': 'Начните утро с улыбки и позитивных мыслей. Уверенность в себе поможет достичь целей.'
            },
            'Телец': {
                'today': 'Телец столкнется с трудностями в налаживании привычного ритма дня, однако, если ему удастся это сделать, то день будет очень плодотворным! Чтобы настроиться на нужную волну, звезды советуют Тельцу с утра принять контрастный душ и послушать бодрящую музыку хотя бы ненадолго. Это поможет преодолеть апатию и задать динамичный, позитивный темп для всего дня. Помимо этого, день прекрасно подойдет для общения с интересными людьми: есть большая вероятность завязать не только приятное знакомство, но и полезное.',
                'love': '❤️ 18%',
                'relationships': '👩❤️💋👨 26%',
                'marriage': '💍 81%',
                'friendship': '🤝 80%',
                'work': '💼 61%',
                'health': '💪 41%',
                'advice': 'Контрастный душ и бодрая музыка зададут тон всему дню. Не упустите шанс полезного знакомства.'
            },
            'Близнецы': {
                'today': 'Сегодня Близнецам особенно повезет в общении с близкими людьми, которые окажут им неоценимую поддержку. Если возникнут проблемы, обращение к родственникам и друзьям принесет больше помощи, чем ожидалось. Но день не только о решении проблем: любое совместное дело с любимыми людьми, будь то дружеская вечеринка или просто семейный ужин, подарит радость и реальную пользу. Будьте искренни с теми, кто вам дорог, и вы увидите, как они с радостью идут навстречу.',
                'love': '❤️ 25%',
                'relationships': '👩❤️💋👨 57%',
                'marriage': '💍 12%',
                'friendship': '🤝 22%',
                'work': '💼 48%',
                'health': '💪 83%',
                'advice': 'Проведите время с близкими. Их поддержка будет очень ценной. Искренность откроет двери.'
            },
            'Рак': {
                'today': 'Сегодня Ракам будет дано ясное понимание своих желаний и предпочтений простых, естественных путей для их достижения. Такая четкость целей и планов впечатляет, но не всегда прямой путь оказывается самым эффективным. Чтобы избежать возможных преград и недоразумений, Ракам стоит рассмотреть альтернативные варианты, а не форсировать события.',
                'love': '❤️ 89%',
                'relationships': '👩❤️💋👨 89%',
                'marriage': '💍 85%',
                'friendship': '🤝 24%',
                'work': '💼 10%',
                'health': '💪 38%',
                'advice': 'Вы четко видите цели, но иногда стоит поискать обходные пути. Не торопитесь.'
            },
            'Лев': {
                'today': 'Сегодня звезды советуют Львам узнать какого-то человека получше: знакомого, коллегу или даже случайного попутчика. Ваши логические способности будут на пике, что позволит получить максимум информации о собеседнике. Вместо пустых разговоров постарайтесь выведать факты биографии и пристрастия, а также поделитесь своими. Это поможет вам установить новый уровень взаимопонимания, который может быть полезен в будущем.',
                'love': '❤️ 26%',
                'relationships': '👩❤️💋👨 72%',
                'marriage': '💍 92%',
                'friendship': '🤝 33%',
                'work': '💼 42%',
                'health': '💪 12%',
                'advice': 'Присмотритесь к окружающим. Глубокое общение принесет пользу в будущем.'
            },
            'Дева': {
                'today': 'Сегодня Дева будет стремиться к однозначности и определенности в любой ситуации. Любая двусмысленность или неопределенность вызовет у нее неприятие и желание всё тщательно проанализировать, расставив все точки над "i". Важно помнить, что не всегда это возможно, а иногда недосказанность может быть более действенным инструментом, чем любые слова.',
                'love': '❤️ 46%',
                'relationships': '👩❤️💋👨 15%',
                'marriage': '💍 88%',
                'friendship': '🤝 10%',
                'work': '💼 35%',
                'health': '💪 85%',
                'advice': 'Стремление к ясности похвально, но иногда недосказанность бывает полезнее.'
            },
            'Весы': {
                'today': 'Весы сегодня преуспеют в вопросах организации и планирования. Составленные вами планы будут простыми и эффективными, а ни одна деталь не останется незамеченной. Однако будьте внимательны к излишней придирчивости: даже незначительные огрехи могут вызвать у вас желание поворчать.',
                'love': '❤️ 52%',
                'relationships': '👩❤️💋👨 70%',
                'marriage': '💍 21%',
                'friendship': '🤝 47%',
                'work': '💼 80%',
                'health': '💪 78%',
                'advice': 'Планируйте, но не будьте слишком придирчивы к мелочам. Сохраняйте спокойствие.'
            },
            'Скорпион': {
                'today': 'Сегодня Скорпиона лучше не провоцировать! Несмотря на кажущуюся покладистость и безмятежность, даже самому Скорпиону сегодня может показаться, что он — само спокойствие и миролюбие. Однако, будьте осторожны — внезапный приступ раздражения может его постигнуть в любой момент. Так что не дразните Скорпиона — лучше сохраняйте мир и покой для всех.',
                'love': '❤️ 45%',
                'relationships': '👩❤️💋👨 41%',
                'marriage': '💍 13%',
                'friendship': '🤝 41%',
                'work': '💼 76%',
                'health': '💪 95%',
                'advice': 'Контролируйте эмоции. Лучший способ избежать конфликтов - сохранять спокойствие.'
            },
            'Стрелец': {
                'today': 'Стрельцы сегодня могут испытывать трудности в общении, поскольку их энергичный ритм жизни будет непонятен для окружающих. Однако Стрельцы будут чувствовать себя полными сил и возможностей! Их деловая активность, находчивость и острый ум позволят им легко справляться с самыми сложными задачами. Негативное отношение и безразличие других могут вызывать раздражение, поэтому Стрельцам лучше сосредоточиться на своих силах и добиваться успеха самостоятельно.',
                'love': '❤️ 50%',
                'relationships': '👩❤️💋👨 19%',
                'marriage': '💍 54%',
                'friendship': '🤝 74%',
                'work': '💼 62%',
                'health': '💪 57%',
                'advice': 'Не обращайте внимание на непонимание окружающих. Сосредоточьтесь на своих целях.'
            },
            'Козерог': {
                'today': 'Сегодня Козерогов ожидает насыщенный день, полный событий! Звезды наполнят его энергией, помогут быстро принимать решения и острым умом разобраться в ситуации. Козерогам будет трудно усидеть на месте, ведь обстоятельства могут требовать их внимания сразу в нескольких местах. Но сам Козерог с радостью примет такой динамичный ритм жизни, ведь кипучая деятельность не только приятна, но и обещает быть полезной: сегодня он может получить неожиданный сюрприз от встреч или событий.',
                'love': '❤️ 37%',
                'relationships': '👩❤️💋👨 76%',
                'marriage': '💍 54%',
                'friendship': '🤝 16%',
                'work': '💼 45%',
                'health': '💪 92%',
                'advice': 'Будьте готовы к насыщенному дню. Возможны приятные сюрпризы и неожиданные встречи.'
            },
            'Водолей': {
                'today': 'Сегодня Водолею стоит обратить внимание на близких людей, готовых оказать ему неоценимую поддержку. Обращение за помощью к родственникам и друзьям гарантирует получение помощи в большем объеме, чем ожидалось. Но помимо решения проблем, этот день благоприятен для любых совместных начинаний с любимыми людьми: будь то дружеская вечеринка или просто семейный вечер. Искренность и открытость в общении помогут Водолею добиться взаимопонимания и получить от близких все необходимое.',
                'love': '❤️ 36%',
                'relationships': '👩❤️💋👨 74%',
                'marriage': '💍 23%',
                'friendship': '🤝 27%',
                'work': '💼 35%',
                'health': '💪 21%',
                'advice': 'Не стесняйтесь обращаться за помощью к близким. Совместные дела принесут радость.'
            },
            'Рыбы': {
                'today': 'Рыбы сегодня смогут взять инициативу в свои руки как в финансовых вопросах, так и в делах сердечных. Звезды благоприятствуют внутреннему равновесию, которое поможет Рыбам добиться успеха во всех начинаниях. Не упустите возможность обсудить с начальником вопрос о повышении зарплаты, но помните — аргументы должны быть вескими и без лишних эмоций.',
                'love': '❤️ 94%',
                'relationships': '👩❤️💋👨 89%',
                'marriage': '💍 11%',
                'friendship': '🤝 66%',
                'work': '💼 93%',
                'health': '💪 55%',
                'advice': 'Берите инициативу в свои руки. Это хороший день для финансовых и сердечных дел.'
            }
        }

        zodiac_info = self.get_zodiac_info(zodiac_sign)
        data = horoscope_data.get(zodiac_sign, horoscope_data['Лев'])

        # Генерируем случайную энергию для разнообразия (но в рамках дня она будет одинаковой для всех пользователей знака)
        random.seed(datetime.now().strftime('%Y-%m-%d'))
        energy = random.randint(60, 100)
        random.seed()  # сброс seed

        return {
            'name': zodiac_sign,
            'emoji': zodiac_info['emoji'],
            'element': zodiac_info['element'],
            'planet': zodiac_info['planet'],
            'date_range': zodiac_info['date_range'],
            'description': zodiac_info['description'],
            'strengths': zodiac_info['strengths'],
            'weaknesses': zodiac_info['weaknesses'],
            'compatibility': zodiac_info['compatibility'],
            'today': data['today'],
            'love': data['love'],
            'relationships': data.get('relationships', ''),
            'marriage': data.get('marriage', ''),
            'friendship': data.get('friendship', ''),
            'career': data.get('work', ''),
            'health': data.get('health', ''),
            'advice': data.get('advice', data['today'][:100] + '...'),
            'lucky_numbers': zodiac_info['lucky_numbers'],
            'lucky_number': random.choice(zodiac_info['lucky_numbers']),
            'lucky_color': zodiac_info['lucky_color'],
            'lucky_color_code': self._get_color_code(zodiac_info['lucky_color']),
            'energy': energy
        }

    def _get_color_code(self, color_name):
        """Вспомогательный метод для получения hex кода цвета по его названию."""
        colors = {
            'Красный': '#ff4444',
            'Зеленый': '#44ff44',
            'Желтый': '#ffff44',
            'Серебряный': '#c0c0c0',
            'Золотой': '#ffd700',
            'Коричневый': '#8b4513',
            'Розовый': '#ff69b4',
            'Бордовый': '#800000',
            'Фиолетовый': '#9b30ff',
            'Черный': '#000000',
            'Синий': '#4444ff',
            'Бирюзовый': '#40e0d0'
        }
        return colors.get(color_name, '#9d7be8')

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

    try:
        from auth import VegaAuth
    except ImportError:
        class VegaAuth:
            def register(self, name, email, pwd1, pwd2, zodiac):
                profile = VegaProfile()
                conn = profile.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (email, password, name, zodiac)
                    VALUES (?, ?, ?, ?)
                ''', (email, pwd1, name, zodiac))
                conn.commit()
                user_id = cursor.lastrowid
                conn.close()
                return True, "OK", {'id': user_id}

    if os.path.exists('vega.db'):
        os.remove('vega.db')
        print("🗑️ Старая БД удалена")

    profile_manager = VegaProfile()

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ ГОРОСКОПОВ VEGA")
    print("=" * 50 + "\n")

    zodiac_signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
                    'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']

    for sign in zodiac_signs:
        print(f"\n📊 {sign}:")
        horo = profile_manager.get_daily_horoscope(sign)
        print(f"   📅 Сегодня: {horo['today'][:60]}...")
        print(f"   💕 Любовь: {horo['love']}")
        print(f"   💼 Карьера: {horo['career']}")
        print(f"   💪 Энергия: {horo['energy']}%")
        print(f"   🍀 Число: {horo['lucky_number']}")
        print("-" * 40)

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 50)