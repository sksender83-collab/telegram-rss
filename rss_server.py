from fastapi import FastAPI
from fastapi.responses import Response
import json
import asyncio
from telethon import TelegramClient
from threading import Thread
import xml.etree.ElementTree as ET

api_id = 29651081
api_hash = "1c5ecefb244fdfdd196b2a7f8ae982ca"

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

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

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

                        # Використовуємо тільки webpage.url для медіа
                        if hasattr(message.media, "webpage") and message.media.webpage:
                            file_url = message.media.webpage.url
                            if file_url:
                                m_type = "video/mp4" if "video" in file_url else "image/jpeg"
                                entry["media"].append({"type": m_type, "url": file_url})

                        # Пропускаємо повідомлення без тексту або без медіа
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
