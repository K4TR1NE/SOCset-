# friends.py - Дополнительные функции для работы с друзьями

def get_friends_list(user_id):
    """Получить список друзей пользователя"""
    # В реальном приложении здесь был бы запрос к базе данных
    friends = [
        {
            'id': 2,
            'name': 'Анна Смирнова',
            'avatar': 'https://randomuser.me/api/portraits/women/44.jpg',
            'zodiac': '♓ Рыбы',
            'is_online': True,
            'mutual_friends': 45
        },
        {
            'id': 3,
            'name': 'Сергей Иванов',
            'avatar': 'https://randomuser.me/api/portraits/men/22.jpg',
            'zodiac': '♏ Скорпион', 
            'is_online': True,
            'mutual_friends': 32
        },
        {
            'id': 4,
            'name': 'Ольга Кузнецова',
            'avatar': 'https://randomuser.me/api/portraits/women/33.jpg',
            'zodiac': '♎ Весы',
            'is_online': False,
            'mutual_friends': 28
        },
        {
            'id': 5,
            'name': 'Дмитрий Соколов',
            'avatar': 'https://randomuser.me/api/portraits/men/55.jpg',
            'zodiac': '♉ Телец',
            'is_online': True,
            'mutual_friends': 56
        }
    ]
    return friends

def get_friend_requests(user_id):
    """Получить заявки в друзья"""
    requests = [
        {
            'id': 6,
            'name': 'Мария Кузнецова',
            'avatar': 'https://randomuser.me/api/portraits/women/68.jpg',
            'mutual_friends': 12,
            'zodiac': '♊ Близнецы'
        }
    ]
    return requests

def accept_friend_request(request_id):
    """Принять заявку в друзья"""
    return {'success': True, 'message': 'Заявка принята!'}

def decline_friend_request(request_id):
    """Отклонить заявку в друзья"""
    return {'success': True, 'message': 'Заявка отклонена'}

def remove_friend(friend_id):
    """Удалить из друзей"""
    return {'success': True, 'message': 'Пользователь удален из друзей'}