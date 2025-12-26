import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

POLZA_API_KEY = os.getenv("POLZA_API_KEY")
API_URL = "https://api.polza.ai/v1/images/generations"  # Проверь этот URL в доках Polza

# Актуальные ID моделей по твоему списку
MODELS_MAP = {
    "nanabanana": "nano-banana",
    "nanabanana_pro": "google/gemini-3-pro-image-preview",
    "seadream": "seedream-v4.5"
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
    if not model_id:
        print(f"❌ Модель {model_type} не найдена в списке")
        return None, None

    headers = {
        "Authorization": f"Bearer {POLZA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_id,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "url"
    }

    # Если бот передает референсное фото
    if image_url:
        payload["image_url"] = image_url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload, timeout=300) as resp:
                if resp.status != 200:
                    print(f"❌ Polza Error: {resp.status}")
                    return None, None

                data = await resp.json()
                # Пытаемся достать URL (проверь формат ответа Polza AI)
                res_url = data.get("image_url") or data.get("data", [{}])[0].get("url")

                if res_url:
                    return await _download_image_bytes(res_url)
    except Exception as e:
        print(f"❌ Ошибка сети: {e}")

    return None, None