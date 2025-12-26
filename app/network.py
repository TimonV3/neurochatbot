import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()

POLZA_API_KEY = os.getenv("POLZA_API_KEY")
BASE_URL = "https://api.polza.ai/api/v1"

# ID моделей согласно твоим справочникам
MODELS_MAP = {
    "nanabanana": "nano-banana",
    "nanabanana_pro": "gemini-3-pro-image-preview",
    "seadream": "seedream-v4"
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

    # 1. Формируем "умный" промпт (Русский + Английский)
    # Это заставляет нейронку лучше понимать задачу и реально изменять фото
    final_prompt = prompt
    if image_url:
        final_prompt = (
            f"Instruction: {prompt}. "
            f"Task: Completely transform and edit the person in this photo according to: {prompt}. "
            f"Style: Realistic, high quality, professional photo edit."
        )

    # 2. Базовый payload
    payload = {
        "model": model_id,
        "prompt": final_prompt,
        "strength": 0.7  # Увеличиваем силу изменений, чтобы не выдавал оригинал
    }

    # 3. Настройка параметров под конкретную модель из документации
    if image_url:
        payload["filesUrl"] = [image_url]

    if model_type == "nanabanana_pro":
        payload["aspect_ratio"] = "1:1"
        payload["resolution"] = "1K"
    elif model_type == "seadream":
        payload["size"] = "1:1"
        payload["imageResolution"] = "1K"
    else:
        payload["size"] = "1:1"
        payload["output_format"] = "png"

    try:
        async with aiohttp.ClientSession() as session:
            # --- ШАГ 1: Создание задачи ---
            async with session.post(f"{BASE_URL}/images/generations", headers=headers, json=payload) as resp:
                data = await resp.json()
                if resp.status not in [200, 201]:
                    print(f"❌ Ошибка API: {resp.status} | {data}")
                    return None, None

                request_id = data.get("requestId")
                if not request_id:
                    print(f"❌ requestId не получен. Ответ: {data}")
                    return None, None

            # --- ШАГ 2: Ожидание результата (Polling) ---
            print(f"⏳ Задача {request_id} в работе. Промпт: {prompt}")

            for i in range(60):  # Ждем до 4 минут
                await asyncio.sleep(4)

                async with session.get(f"{BASE_URL}/images/{request_id}", headers=headers) as s_resp:
                    if s_resp.status != 200:
                        continue

                    result = await s_resp.json()

                    # Проверяем наличие ссылки в разных полях (зависит от модели)
                    res_url = (
                            result.get("url") or
                            (result.get("images")[0] if result.get("images") else None) or
                            (result.get("result", {}).get("url") if isinstance(result.get("result"), dict) else None)
                    )

                    if res_url:
                        print(f"✅ Картинка готова! (итерация {i + 1})")
                        return await _download_image_bytes(res_url)

                    if result.get("status") in ["error", "failed"]:
                        print(f"❌ Polza AI вернула ошибку: {result}")
                        return None, None

            print("❌ Тайм-аут ожидания результата.")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

    return None, None