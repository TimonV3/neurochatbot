from aiohttp import web
from aiogram import Router, types, F
from urllib.parse import urlencode
import os
from app.bot import bot
from app.keyboards.reply import main_kb
import database as db

router = Router()

# URL страницы оплаты из переменных Railway
PRODAMUS_BASE_URL = os.getenv("PRODAMUS_URL", "https://ai-photo-nano.payform.ru")


# --- ВЕБХУК ДЛЯ ПРИЕМА ОПЛАТ ---
async def prodamus_webhook(request):
    """Обработчик уведомлений от Продамуса с записью в таблицу логов"""
    data = await request.post()
    raw_dict = dict(data)

    print(f"DEBUG: Входящий запрос от Prodamus: {raw_dict}")

    payment_status = data.get("payment_status")
    # Берем order_num, так как там лежит формат 'user_id_amount'
    order_data = data.get("order_num")

    # Пытаемся вытащить ID и сумму для лога заранее
    temp_user_id = None
    temp_amount = 0
    if order_data and "_" in str(order_data):
        try:
            p = str(order_data).split("_")
            temp_user_id = int(p[0])
            temp_amount = int(p[1])
        except:
            pass

    if payment_status == "success" and order_data:
        try:
            order_str = str(order_data)

            if "_" not in order_str:
                db.log_payment(temp_user_id, temp_amount, "failed_format", order_str, raw_dict)
                return web.Response(text="Wrong order format", status=200)

            # Парсим финальные значения
            user_id = temp_user_id
            amount = temp_amount

            # 1. Начисляем баланс в Supabase
            db.update_balance(user_id, amount)

            # 2. Фиксируем успешный платеж в новой таблице payment_logs
            db.log_payment(user_id, amount, "success", order_str, raw_dict)

            print(f"✅ УСПЕХ: Начислено {amount} генов пользователю {user_id}")

            # 3. Уведомляем пользователя
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"✅ **Оплата прошла успешно!**\n\n"
                    f"Вам зачислено: `{amount}` ⚡\n"
                    f"Ваш новый баланс: `{db.get_balance(user_id)}` ⚡"
                ),
                reply_markup=main_kb(),
                parse_mode="Markdown"
            )

            return web.Response(text="OK", status=200)

        except Exception as e:
            error_msg = f"error: {str(e)}"
            db.log_payment(temp_user_id, temp_amount, error_msg, str(order_data), raw_dict)
            print(f"❌ ОШИБКА: {error_msg}")
            return web.Response(text="Error", status=500)

    # Если статус не success (например, отмена или ожидание)
    db.log_payment(temp_user_id, temp_amount, f"ignored_{payment_status}", str(order_data), raw_dict)
    return web.Response(text="Ignored", status=200)


# --- ЛОГИКА КНОПОК ТАРИФОВ ---

@router.message(F.text == "💳 Пополнить")
async def show_deposit_menu(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="10 ген. — 149₽", callback_data="pay_10_149")],
        [types.InlineKeyboardButton(text="25 ген. — 375₽", callback_data="pay_25_375")],
        [types.InlineKeyboardButton(text="45 ген. — 675₽", callback_data="pay_45_675")],
        [types.InlineKeyboardButton(text="60 ген. — 900₽", callback_data="pay_60_900")],
    ])

    await message.answer(
        "⚡ **Выберите пакет генераций:**\n\n"
        "Оплата проходит через защищенную систему Prodamus.",
        reply_markup=kb,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("pay_"))
async def create_payment_link(callback: types.CallbackQuery):
    _, amount, price = callback.data.split("_")
    user_id = callback.from_user.id

    params = {
        "do": "pay",
        "order_id": f"{user_id}_{amount}",
        "products[0][name]": f"Пакет {amount} генераций",
        "products[0][price]": price,
        "products[0][quantity]": 1,
        "sys": "telegram_bot"
    }

    payment_url = f"{PRODAMUS_BASE_URL}/?{urlencode(params)}"

    pay_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_url)],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_tariffs")]
    ])

    await callback.message.edit_text(
        f"💎 **Вы выбрали:** {amount} генераций\n"
        f"💰 **Сумма:** {price}₽\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=pay_kb,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_tariffs")
async def back_to_tariffs(callback: types.CallbackQuery):
    await show_deposit_menu(callback.message)
    await callback.answer()