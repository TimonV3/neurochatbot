from aiogram import Router, types, F
import database as db

router = Router()


@router.message(F.text == "👤 Мой баланс")
async def balance(message: types.Message):
    user_id = message.from_user.id
    bal = db.get_balance(user_id)

    # Оформляем красивый вывод профиля
    text = (
        f"👤 **Ваш профиль**\n"
        f"┣ ID: `{user_id}`\n"
        f"┗ Баланс: **{bal}** ⚡\n\n"
        f" _Нажмите на ID, чтобы скопировать его для поддержки._"
    )

    await message.answer(text, parse_mode="Markdown")