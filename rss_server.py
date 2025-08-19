import os
import json
import asyncio
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from fastapi import FastAPI
from mega import Mega
import tempfile
import time

# --- Telegram API ---
api_id = int(os.environ.get("TG_API_ID"))
api_hash = os.environ.get("TG_API_HASH")

# --- Mega.nz ---
MEGA_EMAIL = os.environ.get("MEGA_EMAIL")
MEGA_PASSWORD = os.environ.get("MEGA_PASSWORD")
mega = Mega()
mega.login(MEGA_EMAIL, MEGA_PASSWORD)

# --- Канали ---
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

# --- FastAPI ---
app = FastAPI()

# --- Файли Mega з часом завантаження ---
mega_files = {}  # {link: upload_time}

# --- Функції роботи з last_ids.json ---
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"{STATE_FILE} пошкоджений або порожній. Створюємо новий словник.")
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# --- Завантаження на Mega.nz ---
def upload_to_mega(media_bytes, filename):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(media_bytes)
        tmp_path = tmp.name
    try:
        file = mega.upload(tmp_path, filename)
        link = mega.get_upload_link(file)
        mega_files[link] = time.time()  # зберігаємо час завантаження
    except Exception as e:
        print(f"Помилка завантаження на Mega: {e}")
        link = None
    finally:
        os.remove(tmp_path)
    return link

# --- Фоновий таск видалення файлів старше 1 години ---
async def mega_cleanup_task():
    while True:
        now = time.time()
        to_delete = [link for link, t in mega_files.items() if now - t > 3600]
        for link in to_delete:
            try:
                mega.delete(link)  # видаляємо файл з Mega
            except Exception as e:
                print(f"Помилка видалення Mega файлу {link}: {e}")
            del mega_files[link]
        await asyncio.sleep(600)  # перевірка кожні 10 хвилин

# --- Основна логіка ---
async def fetch_messages(client):
    state = load_state()
    feed_items = []

    for channel in channels:
        try:
            async for message in client.iter_messages(channel, limit=5):
                last_id = state.get(channel, 0)
                if message.id <= last_id:
                    continue

                if not message.text and not message.media:
                    continue

                entry = {
                    "id": message.id,
                    "channel": channel,
                    "text": message.text or "",
                    "media": []
                }

                if hasattr(message.media, "webpage") and message.media.webpage:
                    entry["media"].append({"type": "video", "url": message.media.webpage.url})

                if isinstance(message.media, MessageMediaPhoto) or isinstance(message.media, MessageMediaDocument):
                    try:
                        media_bytes = await message.download_media(bytes)
                        filename = f"{channel}_{message.id}"
                        link = upload_to_mega(media_bytes, filename)
                        if link:
                            media_type = "video" if getattr(message, "video", False) else "image"
                            entry["media"].append({"type": media_type, "url": link})
                    except Exception as e:
                        print(f"Помилка обробки медіа: {e}")

                if entry["text"] or entry["media"]:
                    feed_items.append(entry)

                state[channel] = message.id

        except Exception as e:
            print(f"Помилка при перевірці {channel}: {e}")

    save_state(state)
    return feed_items

# --- FastAPI endpoint ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(mega_cleanup_task())  # запускаємо таск видалення файлів

@app.get("/rss")
async def get_rss():
    async with TelegramClient("anon", api_id, api_hash) as client:
        items = await fetch_messages(client)
        rss = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
        rss += '<title>Telegram RSS</title>\n<link>https://your-render-domain.onrender.com/rss</link>\n'
        rss += '<description>Останні повідомлення з Telegram</description>\n'

        for entry in items:
            rss += f'<item>\n<title>{entry["channel"]} #{entry["id"]}</title>\n'
            rss += f'<description>{entry["text"]}</description>\n'
            for media in entry["media"]:
                rss += f'<enclosure url="{media["url"]}" type="video/mp4" />\n'
            rss += '</item>\n'

        rss += '</channel>\n</rss>'
        return rss
