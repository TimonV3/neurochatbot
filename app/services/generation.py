from app.network import process_with_polza, process_video_polza
import database as db

# Словарь стоимости моделей
COSTS = {
    "nanabanana": 1,
    "nanabanana_pro": 5,
    "seadream": 2,
    "kling_5": 5,   # 5 секунд видео = 5 генераций
    "kling_10": 10  # 10 секунд видео = 10 генераций
}

def cost_for(model: str) -> int:
    """
    Возвращает стоимость генерации для конкретной модели.
    """
    return COSTS.get(model, 1)

def has_balance(user_id: int, cost: int) -> bool:
    """
    Проверяет, достаточно ли у пользователя средств для оплаты.
    """
    return db.get_balance(user_id) >= cost

def charge(user_id: int, cost: int):
    """
    Списывает стоимость с баланса пользователя.
    """
    db.update_balance(user_id, -cost)

async def generate(image_url: str, prompt: str, model: str):
    """
    Основная функция для генерации ИЗОБРАЖЕНИЙ.
    """
    return await process_with_polza(prompt, model, image_url)

async def generate_video(image_url: str, prompt: str, duration: int):
    """
    Основная функция для генерации ВИДЕО (Kling 2.5).
    """
    # Вызываем новую функцию видео из network.py
    return await process_video_polza(prompt, image_url, duration)