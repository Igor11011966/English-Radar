import os
import json
import urllib.request
import urllib.parse
import requests

from gtts import gTTS


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if data:
        data = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def make_audio():
    phrases = []

    words = [
        ("ROAD", "дорога"),
        ("SLIPPERY", "скользкий"),
        ("DELAY", "задержка"),
    ]

    for english, russian in words:

        for i in range(10):
            phrases.append(english)
            phrases.append(russian)

    text = ". ".join(phrases)

    tts = gTTS(
        text=text,
        lang="en"
    )

    tts.save("lesson1.mp3")


def send_audio(chat_id):

    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"

    with open("lesson1.mp3", "rb") as audio:

        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "caption": "🎧 English Radar — урок 1\n\nROAD • SLIPPERY • DELAY"
            },
            files={
                "audio": ("lesson1.mp3", audio, "audio/mpeg")
            }
        )

    print(response.text)


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
                    "🎓 Урок 1 — Дорога\n\n"
                    "Сегодня изучаем:\n\n"
                    "ROAD — дорога\n"
                    "SLIPPERY — скользкий\n"
                    "DELAY — задержка\n\n"
                    "🎧 Сейчас подготовлю аудио."
                ),
            },
        )

        make_audio()
        send_audio(chat_id)

print("English Radar работает.")
