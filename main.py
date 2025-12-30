import asyncio
import os
from aiohttp import web
from aiogram.client.session.aiohttp import AiohttpSession
from app.bot import bot, dp
from app.routers import setup_routers
from app.routers.payments import prodamus_webhook


async def main():
    # 1. Настраиваем роутеры бота
    setup_routers(dp)

    # 2. Настройка веб-сервера
    app = web.Application()
    app.router.add_post("/payments/prodamus", prodamus_webhook)

    runner = web.AppRunner(app)
    await runner.setup()

    # Railway порт
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)

    # 3. Запуск сервера платежей
    await site.start()
    print(f"✅ Сервер платежей запущен на порту {port}")

    # --- ИСПРАВЛЕНИЕ СЕТИ ---
    # Проверяем, есть ли в сессии бота настройки таймаута
    # Если бот инициализирован в другом файле, мы можем переназначить параметры здесь
    print("🚀 Попытка запуска бота...")

    try:
        # Запускаем polling
        # Удаляем лишние запросы при старте, чтобы не ловить таймаут на проверке связи
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        print(f"❌ Ошибка сети или Telegram API: {e}")
    finally:
        # Корректное закрытие всего при выходе
        await bot.session.close()
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Бот и сервер остановлены")