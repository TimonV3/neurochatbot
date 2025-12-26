from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from app.states import PhotoProcess
from app.keyboards.reply import main_kb, cancel_kb
from app.keyboards.inline import model_inline
from app.services.telegram_file import get_telegram_photo_url
from app.services.generation import cost_for, has_balance, generate, charge, generate_video
import database as db

router = Router()


@router.message(F.text == "❌ Отменить")
async def cancel_text(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_kb())


# --- БЛОК ФОТОСЕССИИ (IMAGE-TO-IMAGE) ---

@router.message(F.text == "📸 Начать фотосессию")
async def start_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if db.get_balance(user_id) < 1:
        return await message.answer("❌ У вас недостаточно генераций.")

    await message.answer("🖼 Пришлите фотографию, которую хотите изменить:", reply_markup=cancel_kb())
    await state.set_state(PhotoProcess.waiting_for_photo)


@router.message(PhotoProcess.waiting_for_photo, F.photo)
async def on_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await message.answer("🤖 Выберите нейросеть для обработки:", reply_markup=model_inline())
    await state.set_state(PhotoProcess.waiting_for_model)


@router.callback_query(F.data.startswith("model_"))
async def on_model(callback: types.CallbackQuery, state: FSMContext):
    model = callback.data.replace("model_", "")
    await state.update_data(chosen_model=model)
    model_display = model.replace("_", " ").upper()

    await callback.message.edit_text(f"✅ Выбрана модель: **{model_display}**", parse_mode="Markdown")
    await callback.message.answer(
        "✍️ **Введите описание изменений:**\nНапишите, что именно добавить или изменить.",
        reply_markup=cancel_kb(),
        parse_mode="Markdown"
    )
    await state.set_state(PhotoProcess.waiting_for_prompt)
    await callback.answer()


@router.message(PhotoProcess.waiting_for_prompt)
async def on_prompt(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить": return await cancel_text(message, state)

    user_id = message.from_user.id
    data = await state.get_data()
    model = data.get("chosen_model", "nanabanana")
    cost = cost_for(model)

    if not has_balance(user_id, cost):
        await state.clear()
        return await message.answer(f"❌ Нужно {cost} ген.", reply_markup=main_kb())

    status_msg = await message.answer(f"🚀 Генерация {model.upper()}...", parse_mode="Markdown")

    try:
        photo_url = await get_telegram_photo_url(message.bot, data["photo_id"])
        img_bytes, ext = await generate(photo_url, message.text, model)

        if img_bytes:
            charge(user_id, cost)
            file = BufferedInputFile(img_bytes, filename=f"res.{ext or 'png'}")
            await message.answer_photo(
                photo=file,
                caption=f"✨ **Готово!**\n💰 Списано: {cost} ген.\n🔋 Баланс: {db.get_balance(user_id)} ген.",
                reply_markup=main_kb(),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            await message.answer("❌ Ошибка нейросети. Попробуйте другой промпт.", reply_markup=main_kb())
    except Exception as e:
        print(f"❌ Error in photo: {e}")
        await message.answer("❌ Ошибка системы. Баланс сохранен.")
    finally:
        try:
            await status_msg.delete()
        except:
            pass


# --- БЛОК ОЖИВЛЕНИЯ (IMAGE-TO-VIDEO / KLING 2.5) ---

@router.message(F.text == "🎬 Оживить фото")
async def start_video(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    print(f"DEBUG: Пользователь {user_id} инициировал Kling")

    if db.get_balance(user_id) < 5:
        return await message.answer("❌ Для оживления видео нужно минимум 5 генераций.")

    await message.answer("🎬 Пришлите фото, которое вы хотите оживить:", reply_markup=cancel_kb())
    await state.set_state(PhotoProcess.waiting_for_video_photo)


@router.message(PhotoProcess.waiting_for_video_photo, F.photo)
async def on_video_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 секунд (5 ⚡)", callback_data="v_dur_5")],
        [InlineKeyboardButton(text="10 секунд (10 ⚡)", callback_data="v_dur_10")]
    ])
    await message.answer("⏳ Выберите длительность видео:", reply_markup=kb)
    await state.set_state(PhotoProcess.waiting_for_duration)


@router.callback_query(F.data.startswith("v_dur_"))
async def on_duration(callback: types.CallbackQuery, state: FSMContext):
    duration = int(callback.data.split("_")[2])
    await state.update_data(duration=duration)

    await callback.message.edit_text(
        f"✅ Длительность: **{duration} сек**.\n\n✍️ Опишите движение (например: 'человек смеется'):",
        parse_mode="Markdown"
    )
    await state.set_state(PhotoProcess.waiting_for_video_prompt)
    await callback.answer()


@router.message(PhotoProcess.waiting_for_video_prompt)
async def on_video_prompt(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить":
        return await cancel_text(message, state)

    user_id = message.from_user.id
    data = await state.get_data()
    duration = data.get("duration", 5)
    model_key = f"kling_{duration}"
    cost = cost_for(model_key)

    if not has_balance(user_id, cost):
        return await message.answer(f"❌ Нужно {cost} ген.", reply_markup=main_kb())

    status_msg = await message.answer(
        f"🎬 Оживляю фото (Kling 2.5, {duration}с)...\nПроцесс может занять до 20 минут. Ожидайте.",
        parse_mode="Markdown"
    )

    print(f"DEBUG: Старт генерации видео для {user_id}. Промпт: {message.text}")

    try:
        photo_url = await get_telegram_photo_url(message.bot, data["photo_id"])
        # Вызываем функцию из generation.py
        video_bytes, ext = await generate_video(photo_url, message.text, duration)

        if video_bytes:
            print(f"DEBUG: Видео получено для {user_id}")
            charge(user_id, cost)
            video_file = BufferedInputFile(video_bytes, filename=f"video_{user_id}.mp4")

            await message.answer_video(
                video=video_file,
                caption=f"✅ Видео готово!\n💰 Списано: {cost} ген.\n🔋 Баланс: {db.get_balance(user_id)} ген.",
                reply_markup=main_kb(),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            print(f"DEBUG: Видео НЕ получено (Таймаут/Ошибка) для {user_id}")
            await message.answer(
                "⚠️ Не удалось дождаться видео. Вероятно, сервер перегружен. Попробуйте позже.",
                reply_markup=main_kb()
            )
    except Exception as e:
        print(f"❌ ERROR KLING: {e}")
        await message.answer("❌ Ошибка при создании видео.", reply_markup=main_kb())
    finally:
        try:
            await status_msg.delete()
        except:
            pass