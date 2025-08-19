from telethon import TelegramClient
import json
import os
import asyncio

# Дані Telegram App
api_id = 29651081
api_hash = "1c5ecefb244fdfdd196b2a7f8ae982ca"

# Список каналів
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

# Файл для збереження останніх ID
STATE_FILE = "last_ids.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

async def main():
    state = load_state()

    async with TelegramClient("anon", api_id, api_hash) as client:
        for channel in channels:
            print(f"\n=== Перевіряємо {channel} ===")
            async for message in client.iter_messages(channel, limit=5):
                last_id = state.get(channel, 0)

                if message.id <= last_id:
                    continue

                message_text = message.text if message.text else "[Медіа без тексту]"
                print(f"[NEW] {message.id}: {message_text[:100]}")

                state[channel] = message.id

    save_state(state)

if __name__ == "__main__":
    asyncio.run(main())
