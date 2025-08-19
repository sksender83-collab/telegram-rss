from telethon import TelegramClient
import json
import os
import asyncio
from fastapi import FastAPI
from threading import Thread

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
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
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
                        last_id = state.get(channel, 0)
                        if message.id <= last_id:
                            continue
                        message_text = message.text if message.text else "[Медіа без тексту]"
                        print(f"[{channel}] {message.id}: {message_text[:100]}")
                        state[channel] = message.id
                except Exception as e:
                    print(f"Помилка при перевірці {channel}: {e}")
            save_state(state)
            await asyncio.sleep(60)

# FastAPI веб-сервер
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok"}

# Фоновий запуск Telegram-бота при старті FastAPI
@app.on_event("startup")
def start_telegram_bot():
    def run_loop():
        asyncio.run(check_channels())
    Thread(target=run_loop, daemon=True).start()
