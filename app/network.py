import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()

POLZA_API_KEY = os.getenv("POLZA_API_KEY")
BASE_URL = "https://api.polza.ai/api/v1"

MODELS_MAP = {
    "nanabanana": "nano-banana",
    "nanabanana_pro": "gemini-3-pro-image-preview",
    "seadream": "seedream-v4.5"
}


async def _download_content_bytes(url: str):
    """Универсальная функция скачивания байтов (фото/видео)"""
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=300) as r:
            if r.status == 200:
                content_type = r.headers.get("Content-Type", "").lower()
                # Определяем расширение
                if "video" in content_type:
                    ext = "mp4"
                elif "jpeg" in content_type:
                    ext = "jpg"
                else:
                    ext = "png"
                return await r.read(), ext
    return None, None


async def process_with_polza(prompt: str, model_type: str, image_url: str = None):
    """Существующая функция для фото"""
    if not POLZA_API_KEY:
        return None, None

    model_id = MODELS_MAP.get(model_type)
    headers = {
        "Authorization": f"Bearer {POLZA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_id,
        "prompt": f"{prompt} (High quality photo edit, photorealistic)",
    }

    if image_url:
        payload["filesUrl"] = [image_url]
        payload["strength"] = 0.7

    if model_type == "nanabanana_pro":
        payload["aspect_ratio"] = "1:1"
        payload["resolution"] = "1K"
    elif model_type == "seadream":
        payload["size"] = "1:1"
        payload["imageResolution"] = "1K"
    else:
        payload["size"] = "1:1"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/images/generations", headers=headers, json=payload) as resp:
                data = await resp.json()
                if resp.status not in [200, 201]:
                    print(f"❌ Ошибка API: {data}")
                    return None, None
                request_id = data.get("requestId")
                if not request_id: return None, None

            for i in range(60):
                await asyncio.sleep(4)
                async with session.get(f"{BASE_URL}/images/{request_id}", headers=headers) as s_resp:
                    if s_resp.status != 200: continue
                    result = await s_resp.json()
                    res_url = result.get("url") or (result.get("images")[0] if result.get("images") else None) or (
                        result.get("result", {}).get("url") if isinstance(result.get("result"), dict) else None)
                    if res_url:
                        return await _download_content_bytes(res_url)
                    if result.get("status") in ["error", "failed"]: break
    except Exception as e:
        print(f"❌ Ошибка в network (фото): {e}")
    return None, None


# --- НОВАЯ ФУНКЦИЯ ДЛЯ KLING 2.5 ---

async def process_video_polza(prompt: str, image_url: str, duration: int):
    """
    Генерация видео Kling 2.5 (image-to-video)
    duration: 5 или 10
    """
    if not POLZA_API_KEY:
        return None, None

    headers = {
        "Authorization": f"Bearer {POLZA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "kling2.5-image-to-video",
        "prompt": prompt,
        "duration": duration,
        "imageUrls": [image_url],
        "cfgScale": 0.5
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Запрос на генерацию видео
            async with session.post(f"{BASE_URL}/videos/generations", headers=headers, json=payload) as resp:
                data = await resp.json()
                if resp.status not in [200, 201]:
                    print(f"❌ Ошибка видео API: {data}")
                    return None, None

                request_id = data.get("requestId")
                if not request_id: return None, None

            print(f"⏳ Видео {request_id} в обработке (Kling 2.5)...")

            # 2. Опрос статуса (Polling)
            # Видео генерируется долго, ждем до 15 минут
            for i in range(180):
                await asyncio.sleep(5)
                async with session.get(f"{BASE_URL}/videos/{request_id}", headers=headers) as s_resp:
                    if s_resp.status != 200: continue
                    result = await s_resp.json()

                    # Ищем ссылку на готовое видео
                    video_url = result.get("videoUrl") or (
                        result.get("result") if isinstance(result.get("result"), str) else None)

                    if video_url:
                        print(f"✅ Видео готово!")
                        return await _download_content_bytes(video_url)

                    if result.get("status") in ["error", "failed"]:
                        print(f"❌ Ошибка Kling: {result}")
                        break
    except Exception as e:
        print(f"❌ Ошибка в network (видео): {e}")

    return None, None