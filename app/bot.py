import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from .config import get_settings

settings = get_settings()

# Получаем прокси из переменных окружения
proxy_url = os.getenv("PROXY_URL")

# 1. Настройка сессии
# Добавляем trust_env=True, чтобы aiohttp мог подхватывать системные настройки
session = AiohttpSession(
    timeout=60,
    proxy=proxy_url if proxy_url else None
)

# 2. Настройка кастомного сервера (опционально)
# Если даже с прокси не идет, можно раскомментировать строку ниже для работы через зеркало
# custom_api = TelegramAPIServer.from_base("https://api.tgproxy.me")

bot = Bot(
    token=settings.bot_token,
    session=session,
    # Если используешь зеркало, добавь: server=custom_api
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)

dp = Dispatcher()