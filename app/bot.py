import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from .config import get_settings

settings = get_settings()

# 1. Настраиваем сессию с увеличенным таймаутом
# Это даст боту 60 секунд на ответ от серверов Telegram вместо стандартных 10
# Также добавлена поддержка прокси через переменную окружения (если она есть)
session = AiohttpSession(
    timeout=60,
    proxy=os.getenv("PROXY_URL")  # Можно добавить в настройки Railway, если нужно
)

# 2. Инициализируем бота с использованием новой сессии
bot = Bot(
    token=settings.bot_token,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)

dp = Dispatcher()