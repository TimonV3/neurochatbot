from app.network import process_with_polza
import database as db

# Твои цены
COSTS = {
    "nanabanana": 1,
    "nanabanana_pro": 5,
    "seadream": 2
}

def cost_for(model: str) -> int:
    return COSTS.get(model, 1)

def has_balance(user_id: int, cost: int) -> bool:
    return db.get_balance(user_id) >= cost

def charge(user_id: int, cost: int):
    # Обновляем баланс в минус
    db.update_balance(user_id, -cost)

async def generate(image_url: str, prompt: str, model: str):
    """
    Основная функция вызова из роутера
    """
    return await process_with_polza(prompt, model, image_url)