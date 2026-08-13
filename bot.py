import os
import json
import urllib.request
import urllib.parse
import requests
import tempfile

from gtts import gTTS
from pydub import AudioSegment


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if data:
        data = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def make_audio():

    words = [
        ("ROAD", "дорога"),
        ("SLIPPERY", "скользкий"),
        ("DELAY", "задержка"),
    ]

    result = AudioSegment.empty()

    pause_after_english = AudioSegment.silent(duration=1000)
    pause_after_russian = AudioSegment.silent(duration=1500)

    for english, russian in words:

        for i in range(10):

            with tempfile.NamedTemporaryFile(suffix=".mp3") as en_file:
                gTTS(
                    text=english,
                    lang="en",
                    slow=True
                ).save(en_file.name)

                english_audio = AudioSegment.from_mp3(en_file.name)

            with tempfile.NamedTemporaryFile(suffix=".mp3") as ru_file:
                gTTS(
                    text=russian,
                    lang="ru",
                    slow=True
                ).save(ru_file.name)

                russian_audio = AudioSegment.from_mp3(ru_file.name)

            result += english_audio
            result += pause_after_english
            result += russian_audio
            result += pause_after_russian

    result.export("lesson1.mp3", format="mp3")


def send_audio(chat_id):

    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"

    with open("lesson1.mp3", "rb") as audio:

        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "caption": (
                    "🎧 English Radar — Урок 1\n\n"
                    "ROAD • SLIPPERY • DELAY\n"
                    "10 повторений каждого слова"
                )
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
                    "ROAD — дорога\n"
                    "SLIPPERY — скользкий\n"
                    "DELAY — задержка\n\n"
                    "🎧 Аудио подготовлено.\n"
                    "Каждое слово — 10 повторений."
                ),
            },
        )

        make_audio()
        send_audio(chat_id)


print("English Radar работает.")
