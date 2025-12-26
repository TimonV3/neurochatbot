from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# --- Выбор модели генерации изображения ---
def model_inline() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора модели ИИ для генерации фото.
    Цены отражены для удобства пользователя.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🍌 NanoBanana (1 ген.)",
                callback_data="model_nanabanana"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚡ NanoBanana PRO (5 ген.)",
                callback_data="model_nanabanana_pro"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌊 Seedream 4.5 (2 ген.)",
                callback_data="model_seadream"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel"
            )
        ]
    ])


# --- Кнопки пополнения баланса ---
def buy_inline() -> InlineKeyboardMarkup:
    """
    Пакеты оплаты. Названия кнопок можно менять,
    главное — callback_data сохраняем.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10 ген. — 149₽", callback_data="pay_10_149")],
        [InlineKeyboardButton(text="25 ген. — 375₽", callback_data="pay_25_375")],
        [InlineKeyboardButton(text="45 ген. — 675₽", callback_data="pay_45_675")],
        [InlineKeyboardButton(text="60 ген. — 900₽", callback_data="pay_60_900")],
    ])
