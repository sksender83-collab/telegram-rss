import os
import time
import asyncio
from fastapi import FastAPI, Response
from telethon import TelegramClient
from threading import Thread
import xml.etree.ElementTree as ET
from mega import Mega

# Telegram API
import os

api_id = int(os.environ.get("TG_API_ID"))
api_hash = os.environ.get("TG_API_HASH")

channels = [
    "https://t.me/lviv_nez",
    "https://t.me/lvivtruexa",
    "https://t.me/lviv_ukraine",
    "https://t.me/lvivtp",
    "https://t.me/lviv_tviy",
    "https://t.me/lvivshchyna_news",
    "https://t.me/lviv_lmbrg",
    "https://t.me/lviv_realno",
    "https://t.me/lvov_lviv_novini",
    "https://t.me/times_lviv",
    "https://t.me/vistilviv",
    "https://t.me/lviv_golovne",
    "https://t.me/lviv_24x7"
]

STATE_FILE = "last_ids.json"

# Mega.nz через змінні середовища
MEGA_EMAIL = os.environ.get("MEGA_EMAIL")
MEGA_PASSWORD = os.environ.get("MEGA_PASSWORD")
mega = Mega()
mega.login(MEGA_EMAIL, MEGA_PASSWORD)

# Час життя файлу на Mega (секунди)
MEDIA_LIFETIME = 60 * 60  # 1 година

def load_state():
    try:
        import json
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    import json
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def delete_file_after_delay(file):
    time.sleep(MEDIA_LIFETIME)
    try:
        mega.delete(file)
        print(f"Файл {file} видалено після {MEDIA_LIFETIME} секунд.")
    except Exception as e:
        print(f"Помилка при видаленні файлу з Mega.nz: {e}")

async def check_channels():
    state = load_state()
    async with TelegramClient("anon", api_id, api_hash) as client:
        while True:
            for channel in channels:
                try:
                    async for message in client.iter_messages(channel, limit=5):
                        last_entry = state.get(channel, {"id": 0, "text": "", "media": []})
                        if isinstance(last_entry, int):
                            last_entry = {"id": last_entry, "text": "", "media": []}

                        if message.id <= last_entry["id"]:
                            continue

                        entry = {"id": message.id, "text": message.text or "", "media": []}

                        # Обробка всіх медіа
                        if message.media:
                            try:
                                # Локальний файл для завантаження
                                local_filename = f"{channel.split('/')[-1]}_{message.id}"
                                local_path = await client.download_media(message.media, file=local_filename)

                                if local_path:
                                    # Визначаємо тип медіа
                                    ext = os.path.splitext(local_path)[1].lower()
                                    if ext in [".mp4", ".mov", ".webm"]:
                                        media_type = "video/mp4"
                                    elif ext in [".jpg", ".jpeg", ".png", ".gif"]:
                                        media_type = "image/jpeg"
                                    else:
                                        media_type = "application/octet-stream"

                                    # Завантаження на Mega.nz
                                    file = mega.upload(local_path)
                                    mega_url = mega.get_upload_link(file)
                                    entry["media"].append({"type": media_type, "url": mega_url})

                                    Thread(target=delete_file_after_delay, args=(file,)).start()
                                    os.remove(local_path)
                            except Exception as e:
                                print(f"Помилка при обробці медіа: {e}")

                        # Пропускаємо пости без тексту та медіа
                        if not entry["text"] or not entry["media"]:
                            continue

                        state[channel] = entry
                        print(f"[{channel}] {message.id}: {entry['text'][:100]}")

                except Exception as e:
                    print(f"Помилка при перевірці {channel}: {e}")

            save_state(state)
            await asyncio.sleep(60)

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.get("/rss")
def get_rss():
    state = load_state()
    rss = ET.Element("rss", version="2.0")
    channel_el = ET.SubElement(rss, "channel")
    ET.SubElement(channel_el, "title").text = "Telegram RSS"
    ET.SubElement(channel_el, "link").text = "https://your-render-domain.onrender.com/rss"
    ET.SubElement(channel_el, "description").text = "Останні повідомлення з Telegram"

    for channel_name, data in state.items():
        if isinstance(data, int):
            continue
        text = data.get("text", "")
        media = data.get("media", [])
        if not text or not media:
            continue
        item = ET.SubElement(channel_el, "item")
        ET.SubElement(item, "title").text = f"{channel_name} - {data['id']}"
        ET.SubElement(item, "description").text = text
        ET.SubElement(item, "link").text = f"{channel_name}/{data['id']}"
        for m in media:
            ET.SubElement(item, "enclosure", url=m["url"], type=m["type"])

    xml_str = ET.tostring(rss, encoding="utf-8")
    return Response(content=xml_str, media_type="application/rss+xml")

@app.on_event("startup")
def start_telegram_bot():
    def run_loop():
        asyncio.run(check_channels())
    Thread(target=run_loop, daemon=True).start()
