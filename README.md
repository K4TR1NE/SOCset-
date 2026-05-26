# ✦ V E G Λ ✦ — Астрологическая социальная сеть

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.0+-green?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/SQLite-3-blue?logo=sqlite" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen" alt="Status">
</p>

<p align="center">
  <b>Уникальная платформа, объединяющая людей по интересам к астрологии, эзотерике и самопознанию</b>
</p>

---

## 📖 О проекте

**VEGA** — это социальная сеть нового поколения с астрологическим уклоном. Здесь вы можете делиться мыслями, находить друзей по знаку зодиака, получать ежедневные гороскопы, создавать сообщества и многое другое.

### ✨ Основные возможности

| Функция | Описание |
|:--------|:---------|
| 🔐 **Авторизация** | Регистрация по телефону + гостевой режим |
| 📝 **Лента постов** | Создание постов с Rich-текстом (TinyMCE), фото и видео |
| ❤️ **Взаимодействие** | Лайки, комментарии, репосты на стену или другу |
| 👥 **Друзья** | Отправка/приём заявок, список друзей, онлайн-статусы |
| 💬 **Чат** | Личные сообщения с уведомлениями (polling) |
| 🌙 **Гороскопы** | Персональные гороскопы по знаку зодиака |
| 📅 **Календарь** | Праздники + личные события, динамическая Пасха/Масленица |
| 🖼️ **Галерея** | Загрузка фото/видео, drag&drop, просмотр в модальном окне |
| 🏘️ **Сообщества** | Группы по интересам с фильтрацией |
| 🎨 **Темы оформления** | Светлая/тёмная тема, настройка размера шрифта и акцентного цвета |
| 🔒 **Приватность** | Настройки видимости профиля и сообщений |

---

## 🚀 Быстрый старт

### Требования

- Python 3.9 или выше
- pip (менеджер пакетов Python)

### Установка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/vega-social.git
cd vega-social

# 2. Создайте виртуальное окружение (рекомендуется)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Установите зависимости
pip install flask werkzeug

# 4. Запустите приложение
python app.py
Доступ
Откройте браузер и перейдите по адресу: http://127.0.0.1:5000

При первом запуске автоматически создадутся все таблицы базы данных и предустановленные праздники.

📁 Структура проекта
text
vega-social/
├── app.py                 # Главный файл приложения (Flask routes)
├── auth.py                # Класс VegaAuth (пользователи, друзья, посты, чаты, репосты)
├── profile.py             # Класс VegaProfile (управление профилем, хобби, подсказки)
├── events.py              # Класс VegaEvents (календарь, праздники, события)
│
├── templates/             # HTML-шаблоны (Jinja2)
│   ├── layout.html        # Базовый шаблон (главная сетка, темы, поиск)
│   ├── index.html         # Главная лента (посты, TinyMCE, лайки, комменты)
│   ├── login.html         # Страница входа (телефон + гость)
│   ├── register.html      # Страница регистрации
│   ├── profile.html       # Личный профиль + гороскоп
│   ├── user_profile.html  # Профиль другого пользователя
│   ├── friends.html       # Управление друзьями (3 вкладки)
│   ├── chat.html          # Личные сообщения (с карточками репостов)
│   ├── communities.html   # Сообщества (фильтры по категориям)
│   ├── gallery.html       # Галерея (загрузка фото/видео, drag&drop)
│   ├── events.html        # Календарь событий + модалка добавления
│   ├── settings.html      # Настройки (тема, шрифт, приватность)
│   ├── terms.html         # Условия использования
│   ├── privacy.html       # Политика конфиденциальности
│   ├── about.html         # О проекте
│   ├── contacts.html      # Контакты
│   └── team.html          # Команда
│
├── static/uploads/        # Загруженные аватары и медиафайлы
│
├── vega.db                # SQLite база данных (создаётся автоматически)
│
└── README.md              # Этот файл
🗄️ База данных
Основные таблицы
Таблица	Описание
users	Пользователи (логин, пароль, аватар, знак зодиака, статус, настройки приватности)
posts	Посты (текст, лайки, комментарии, репосты, привязка к стене пользователя)
friends	Дружеские связи (статус: pending/accepted)
messages	Личные сообщения (с поддержкой репостов)
likes	Лайки на постах
comments	Комментарии к постам
gallery	Медиафайлы (фото/видео) с привязкой к постам
events	События (праздники и личные)
user_settings	Настройки пользователя (тема, размер шрифта, приватность)
🎨 Технологии
Backend
Flask — веб-фреймворк

SQLite3 — база данных

Werkzeug — безопасная работа с файлами

Frontend
HTML5 / CSS3 — адаптивная вёрстка

JavaScript (ES6) — интерактивность

TinyMCE — визуальный редактор постов

Font Awesome 6 — иконки

Особенности реализации
🔐 CSRF-защита форм

📁 Безопасная загрузка файлов (проверка расширений и размера)

🌙 Светлая/тёмная тема с сохранением в localStorage и БД

📱 Адаптивный дизайн (мобильные устройства)

👤 Гостевой режим без регистрации

🔄 Репосты на стену и другу (с карточками в чате)

🖼️ Просмотр фото в модальном окне с навигацией

🔧 Основные API маршруты
Метод	Маршрут	Описание
GET	/	Главная лента
GET/POST	/login	Вход (телефон + пароль / гость)
GET/POST	/register	Регистрация
GET	/profile	Личный профиль
GET	/user/<id>	Профиль пользователя
POST	/create_post	Создание поста
POST	/like_post/<id>	Лайк/анлайк поста
POST	/add_comment/<id>	Добавление комментария
POST	/create_repost	Репост на свою стену
POST	/send_repost_to_chat	Репост другу в чат
GET	/chat	Страница чата
POST	/send_message	Отправка сообщения
GET	/friends	Страница друзей
POST	/upload_to_gallery	Загрузка в галерею
GET	/events	Календарь событий
POST	/save_settings	Сохранение настроек
GET	/search	Поиск пользователей
🖼️ Скриншоты
Главная лента	Профиль	Чат
https://via.placeholder.com/300x200?text=Feed	https://via.placeholder.com/300x200?text=Profile	https://via.placeholder.com/300x200?text=Chat
👥 Команда
Участник	Роль
Возисов Аретмий Вадимович	Руководитель проекта
Овчинников Максим Александрович	Старший фронтенд-разработчик
Трефилов Семён Андреевич	Бэкенд-разработчик
📞 Контакты
Email: vega@social.ru

Telegram: @vega_social

GitHub: github.com/vega-social

📄 Лицензия
Проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.

🙏 Благодарности
Unsplash — изображения для демонстрации

Font Awesome — иконки

TinyMCE — текстовый редактор

RandomUser.me — тестовые аватары

<p align="center"> <b>Присоединяйтесь к VEGA — здесь каждый найдёт свою звезду! ✨</b> </p> ```
📁 Дополнительно создайте файл LICENSE (MIT):
markdown
MIT License

Copyright (c) 2026 VEGA Social Network

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
📁 Создайте файл .gitignore:
gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Database
*.db
*.sqlite
*.sqlite3

# Uploads
static/uploads/*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
🚀 Как загрузить на GitHub
bash
# 1. Инициализируйте Git репозиторий
git init

# 2. Добавьте все файлы
git add .

# 3. Создайте коммит
git commit -m "Initial commit: VEGA Social Network v1.0"

# 4. Добавьте удалённый репозиторий
git remote add origin https://github.com/yourusername/vega-social.git

# 5. Отправьте код
git push -u origin main
Теперь ваш проект VEGA готов к публикации на GitHub!


