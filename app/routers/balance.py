from aiogram import Router, types, F
import database as db

router = Router()


@router.message(F.text == "👤 Мой баланс")
async def balance(message: types.Message):
    user_id = message.from_user.id
    bal = db.get_balance(user_id)

    # 1. Получаем количество приглашенных друзей
    ref_count = db.get_referrals_count(user_id)

    # 2. Формируем реферальную ссылку
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    # 3. Оформляем вывод с реферальной программой
    text = (
        f"👤 **Ваш профиль**\n"
        f"┣ ID: `{user_id}`\n"
        f"┗ Баланс: **{bal}** ⚡\n\n"
        f"👥 **Приглашено друзей:** `{ref_count}`\n\n"
        f"🎁 **Реферальная программа:**\n"
        f"Приглашайте друзей и получайте **10%** от их покупок!\n\n"
        f"🔗 **Ваша ссылка:**\n`{ref_link}`\n\n"
        f"_Нажмите на ID или ссылку, чтобы скопировать._"
    )

    await message.answer(text, parse_mode="Markdown")