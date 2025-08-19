from telethon import TelegramClient
import json
import os
import asyncio
from telethon.errors import FloodWaitError, ChannelPrivateError, ChannelInvalidError

# Дані твого Telegram App
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
    """Завантажуємо останні ID з файлу"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Помилка при завантаженні файлу стану: {e}")
        return {}

def save_state(state):
    """Зберігаємо останні ID у файл"""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Помилка при збереженні файлу стану: {e}")

async def main():
    state = load_state()

    for channel in channels:
        print(f"\n=== Перевіряємо {channel} ===")
        try:
            # Отримуємо останні 5 постів
            async for message in client.iter_messages(channel, limit=5):
                last_id = state.get(channel, 0)

                if message.id <= last_id:
                    # Це старе повідомлення, пропускаємо
                    continue

                # Перевіряємо, чи є текст у повідомленні
                message_text = message.text if message.text else "[Медіа без тексту]"
                print(f"[NEW] {message.id}: {message_text[:100]}")

                # Оновлюємо ID
                state[channel] = message.id

            # Затримка, щоб уникнути FloodWaitError
            await asyncio.sleep(1)

        except (ChannelPrivateError, ChannelInvalidError):
            print(f"Помилка: Канал {channel} приватний або недійсний")
        except FloodWaitError as e:
            print(f"Обмеження Telegram, чекаємо {e.seconds} секунд")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"Помилка при обробці каналу {channel}: {e}")

    save_state(state)

# Запускаємо клієнт
async def run_client():
    try:
        async with TelegramClient("anon", api_id, api_hash) as client:
            await main()
    except Exception as e:
        print(f"Помилка ініціалізації клієнта: {e}")

# Запускаємо асинхронний код
if __name__ == "__main__":
    asyncio.run(run_client())
