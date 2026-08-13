import os
import json
import urllib.request
import urllib.parse

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if data:
        data = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


# Проверяем работу бота
updates = telegram("getUpdates")

for update in updates.get("result", []):

    message = update.get("message")

    if not message:
        continue

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/start"):

        telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": (
                    "🇬🇧 ENGLISH RADAR\n\n"
                    "🚛 Урок 1 — Дорога\n\n"
                    "Сегодня изучаем 3 слова:\n\n"
                    "ROAD — дорога\n"
                    "SLIPPERY — скользкий\n"
                    "DELAY — задержка\n\n"
                    "Скоро начинаем повторение."
                ),
            },
        )

print("English Radar работает.")
