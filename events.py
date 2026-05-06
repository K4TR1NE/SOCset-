# events.py - Система управления событиями VEGA

import sqlite3
from datetime import datetime, timedelta
import json


class VegaEvents:
    """Класс для работы с событиями и календарем"""

    def __init__(self, db_name='vega.db'):
        self.db_name = db_name
        self.init_events_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_events_tables(self):
        """Создание таблиц для событий"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица событий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                event_date TEXT NOT NULL,
                event_type TEXT DEFAULT 'personal',
                color TEXT DEFAULT '#9d7be8',
                icon TEXT DEFAULT 'fa-star',
                is_public INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        conn.commit()
        conn.close()

        # Добавляем предустановленные праздники, если таблица пуста
        self.add_default_holidays()

    def add_default_holidays(self):
        """Добавление стандартных праздников"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM events WHERE event_type = ?', ('holiday',))
        if cursor.fetchone()['count'] > 0:
            conn.close()
            return

        current_year = datetime.now().year

        holidays = [
            {
                'title': 'Новый год',
                'description': 'Встреча Нового года! 🎄',
                'date': f'{current_year}-01-01',
                'color': '#ff6b8b',
                'icon': 'fa-tree',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'Рождество Христово',
                'description': 'Православное Рождество ✨',
                'date': f'{current_year}-01-07',
                'color': '#ffb86b',
                'icon': 'fa-star',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'Старый Новый год',
                'description': 'Старый Новый год 🎉',
                'date': f'{current_year}-01-14',
                'color': '#c77dff',
                'icon': 'fa-champagne-glasses',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'День всех влюбленных',
                'description': 'День святого Валентина 💝',
                'date': f'{current_year}-02-14',
                'color': '#ff6b8b',
                'icon': 'fa-heart',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'День защитника Отечества',
                'description': '23 февраля 🎖️',
                'date': f'{current_year}-02-23',
                'color': '#8a9eff',
                'icon': 'fa-shield',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'Масленица',
                'description': 'Проводы зимы 🥞',
                'date': f'{current_year}-03-17',
                'color': '#ffb86b',
                'icon': 'fa-sun',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'Международный женский день',
                'description': '8 Марта 💐',
                'date': f'{current_year}-03-08',
                'color': '#ff6b8b',
                'icon': 'fa-flower',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'День космонавтики',
                'description': '12 апреля 🚀',
                'date': f'{current_year}-04-12',
                'color': '#8a9eff',
                'icon': 'fa-rocket',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'Пасха',
                'description': 'Светлое Христово Воскресение 🥚',
                'date': f'{current_year}-04-20',
                'color': '#ffb86b',
                'icon': 'fa-egg',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'Праздник Весны и Труда',
                'description': '1 Мая 🌸',
                'date': f'{current_year}-05-01',
                'color': '#8a9eff',
                'icon': 'fa-leaf',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'День Победы',
                'description': '9 Мая - День Великой Победы! 🎗️',
                'date': f'{current_year}-05-09',
                'color': '#ff6b8b',
                'icon': 'fa-ribbon',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'День России',
                'description': '12 июня 🇷🇺',
                'date': f'{current_year}-06-12',
                'color': '#8a9eff',
                'icon': 'fa-flag',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'День знаний',
                'description': '1 сентября 📚',
                'date': f'{current_year}-09-01',
                'color': '#ffb86b',
                'icon': 'fa-book',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'День народного единства',
                'description': '4 ноября 🤝',
                'date': f'{current_year}-11-04',
                'color': '#8a9eff',
                'icon': 'fa-handshake',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'Хэллоуин',
                'description': '31 октября 🎃',
                'date': f'{current_year}-10-31',
                'color': '#ffb86b',
                'icon': 'fa-ghost',
                'type': 'holiday',
                'is_public': 1
            },
            {
                'title': 'Новый год (следующий)',
                'description': 'Встреча Нового года! 🎄',
                'date': f'{current_year + 1}-01-01',
                'color': '#ff6b8b',
                'icon': 'fa-tree',
                'type': 'holiday',
                'is_public': 1
            }
        ]

        for holiday in holidays:
            cursor.execute('''
                INSERT INTO events (user_id, title, description, event_date, event_type, color, icon, is_public)
                VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
            ''', (holiday['title'], holiday['description'], holiday['date'],
                  holiday['type'], holiday['color'], holiday['icon'], holiday['is_public']))

        conn.commit()
        conn.close()
        print("✅ Предустановленные праздники добавлены")

    def get_events_by_month(self, year, month, user_id=None):
        """Получить события за месяц"""
        conn = self.get_connection()
        cursor = conn.cursor()

        start_date = f'{year}-{month:02d}-01'
        if month == 12:
            end_date = f'{year}-12-31'
        else:
            end_date = f'{year}-{month + 1:02d}-01'

        # Общие праздники + личные события пользователя
        if user_id:
            cursor.execute('''
                SELECT * FROM events 
                WHERE event_date >= ? AND event_date < ?
                AND (is_public = 1 OR user_id = ?)
                ORDER BY event_date ASC
            ''', (start_date, end_date, user_id))
        else:
            cursor.execute('''
                SELECT * FROM events 
                WHERE event_date >= ? AND event_date < ?
                AND is_public = 1
                ORDER BY event_date ASC
            ''', (start_date, end_date))

        events = [dict(e) for e in cursor.fetchall()]
        conn.close()
        return events

    def get_events_by_date(self, date_str, user_id=None):
        """Получить события на конкретную дату"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute('''
                SELECT * FROM events 
                WHERE event_date = ?
                AND (is_public = 1 OR user_id = ?)
                ORDER BY event_type DESC
            ''', (date_str, user_id))
        else:
            cursor.execute('''
                SELECT * FROM events 
                WHERE event_date = ? AND is_public = 1
                ORDER BY event_type DESC
            ''', (date_str,))

        events = [dict(e) for e in cursor.fetchall()]
        conn.close()
        return events

    def add_event(self, user_id, title, date_str, description='', color='#9d7be8', icon='fa-calendar'):
        """Добавить личное событие"""
        if not title or not date_str:
            return False, "Название и дата обязательны"

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO events (user_id, title, description, event_date, event_type, color, icon, is_public)
            VALUES (?, ?, ?, ?, 'personal', ?, ?, 0)
        ''', (user_id, title, description, date_str, color, icon))

        conn.commit()
        event_id = cursor.lastrowid
        conn.close()

        return True, "Событие добавлено!", event_id

    def update_event(self, event_id, user_id, data):
        """Обновить событие"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Проверяем, что событие принадлежит пользователю
        cursor.execute('SELECT * FROM events WHERE id = ? AND user_id = ?', (event_id, user_id))
        if not cursor.fetchone():
            conn.close()
            return False, "Событие не найдено или нет прав на редактирование"

        updates = {}
        for field in ['title', 'description', 'event_date', 'color', 'icon']:
            if field in data and data[field]:
                updates[field] = data[field]

        if not updates:
            conn.close()
            return False, "Нет данных для обновления"

        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values()) + [event_id]

        cursor.execute(f'UPDATE events SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()

        return True, "Событие обновлено!"

    def delete_event(self, event_id, user_id):
        """Удалить событие"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM events WHERE id = ? AND user_id = ?', (event_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "Событие не найдено или нет прав на удаление"

        conn.commit()
        conn.close()
        return True, "Событие удалено!"

    def get_calendar_data(self, year, month, user_id=None):
        """Получить данные для календаря"""
        import calendar

        cal = calendar.monthcalendar(year, month)
        events = self.get_events_by_month(year, month, user_id)

        # Группируем события по дням
        events_by_day = {}
        for event in events:
            day = int(event['event_date'].split('-')[2])
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)

        return {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'calendar': cal,
            'events': events_by_day,
            'today': datetime.now().day if datetime.now().month == month and datetime.now().year == year else None
        }

    def get_upcoming_events(self, user_id=None, limit=10):
        """Получить ближайшие события"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        if user_id:
            cursor.execute('''
                SELECT * FROM events 
                WHERE event_date >= ?
                AND (is_public = 1 OR user_id = ?)
                ORDER BY event_date ASC
                LIMIT ?
            ''', (today, user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM events 
                WHERE event_date >= ? AND is_public = 1
                ORDER BY event_date ASC
                LIMIT ?
            ''', (today, limit))

        events = [dict(e) for e in cursor.fetchall()]
        conn.close()
        return events


# ======================
# ТЕСТИРОВАНИЕ
# ======================

if __name__ == '__main__':
    import os

    if os.path.exists('vega.db'):
        os.remove('vega.db')

    from good import VegaAuth

    auth = VegaAuth()
    events_manager = VegaEvents()

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ СОБЫТИЙ")
    print("=" * 50)

    # Создаем пользователя
    success, msg, user = auth.register("Тест", "test@test.ru", "pass123", "pass123", "Лев")
    if success:
        user_id = user['id']

        # Тест 1: Добавление личного события
        print("\n📅 Тест 1: Добавление события")
        success, msg, event_id = events_manager.add_event(
            user_id, "День рождения друга", "2025-03-15", "Не забыть поздравить!", "#ff6b8b", "fa-cake-candles"
        )
        print(f"{'✅' if success else '❌'} {msg}")

        # Тест 2: Получение событий на месяц
        print("\n📅 Тест 2: События на март")
        events = events_manager.get_events_by_month(2025, 3, user_id)
        print(f"✅ Найдено событий: {len(events)}")

        # Тест 3: Ближайшие события
        print("\n📅 Тест 3: Ближайшие события")
        upcoming = events_manager.get_upcoming_events(user_id)
        print(f"✅ Ближайших событий: {len(upcoming)}")
        for e in upcoming[:3]:
            print(f"  • {e['event_date']}: {e['title']}")

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")