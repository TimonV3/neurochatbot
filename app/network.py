import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()

POLZA_API_KEY = os.getenv("POLZA_API_KEY")
BASE_URL = "https://api.polza.ai/api/v1"

# Актуальные ID моделей из твоих справочников
MODELS_MAP = {
    "nanabanana": "nano-banana",
    "nanabanana_pro": "gemini-3-pro-image-preview",
    "seadream": "seedream-v4"  # В доке 4.0 указано v4
}


async def _download_image_bytes(url: str):
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=120) as r:
            if r.status == 200:
                content_type = r.headers.get("Content-Type", "").lower()
                ext = "jpg" if "jpeg" in content_type else "png"
                return await r.read(), ext
    return None, None


async def process_with_polza(prompt: str, model_type: str, image_url: str = None):
    if not POLZA_API_KEY:
        print("❌ POLZA_API_KEY не задан")
        return None, None

    model_id = MODELS_MAP.get(model_type)
    headers = {
        "Authorization": f"Bearer {POLZA_API_KEY}",
        "Content-Type": "application/json"
    }

    # Базовый payload
    payload = {
        "model": model_id,
        "prompt": prompt
    }

    # Добавляем фото, если оно есть (массив по доке)
    if image_url:
        payload["filesUrl"] = [image_url]

    # Настройка параметров под конкретную модель
    if model_type == "nanabanana_pro":
        payload["aspect_ratio"] = "1:1"
        payload["resolution"] = "1K"
    elif model_type == "seadream":
        payload["size"] = "1:1"
        payload["imageResolution"] = "1K"
    else:  # обычная nanabanana
        payload["size"] = "1:1"

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Отправка генерации
            async with session.post(f"{BASE_URL}/images/generations", headers=headers, json=payload) as resp:
                data = await resp.json()
                if resp.status not in [200, 201]:
                    print(f"❌ Ошибка старта: {resp.status} | {data}")
                    return None, None

                request_id = data.get("requestId")
                if not request_id:
                    print(f"❌ ID не получен: {data}")
                    return None, None

            # 2. Опрос статуса по эндпоинту /api/v1/images/{id}
            print(f"⏳ Задача {request_id} ({model_type}) в работе...")

            for i in range(60):  # Ждем до 4 минут (на 4К может быть долго)
                await asyncio.sleep(4)

                async with session.get(f"{BASE_URL}/images/{request_id}", headers=headers) as s_resp:
                    if s_resp.status != 200:
                        continue

                    result = await s_resp.json()

                    # Логика поиска ссылки в ответе
                    # Polza может вернуть или в корне 'url', или в массиве 'images'
                    res_url = result.get("url")
                    if not res_url and "images" in result and result["images"]:
                        res_url = result["images"][0]
                    if not res_url and "result" in result:
                        if isinstance(result["result"], str):
                            res_url = result["result"]
                        elif isinstance(result["result"], dict):
                            res_url = result["result"].get("url")

                    if res_url:
                        print(f"✅ Успешно! Итерация {i + 1}")
                        return await _download_image_bytes(res_url)

                    # Если API вернуло статус ошибки
                    if result.get("status") in ["error", "failed"]:
                        print(f"❌ Ошибка выполнения в API: {result}")
                        return None, None

            print("❌ Время ожидания истекло.")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    return None, None