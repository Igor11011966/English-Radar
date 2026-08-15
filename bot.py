import os
import json
import urllib.request
import urllib.parse
import requests
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

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


# =========================================================
# НАШИ СЛОВА
# =========================================================

WORDS = [
    {
        "en": "ROAD",
        "ru": "дорога",
        "association": "ROAD звучит примерно как «РОУД» — представь ДОРОГУ перед собой."
    },
    {
        "en": "SLIPPERY",
        "ru": "скользкий",
        "association": "SLIPPERY — представь скользкую дорогу после дождя."
    },
    {
        "en": "DELAY",
        "ru": "задержка",
        "association": "DELAY — представь, что грузовик задержался в пути."
    }
]


# =========================================================
# АУДИО
# =========================================================

def make_audio(stage):

    result = AudioSegment.empty()

    pause_short = AudioSegment.silent(duration=900)
    pause_long = AudioSegment.silent(duration=1600)

    for word in WORDS:

        english = word["en"]
        russian = word["ru"]

        # -------------------------------------------------
        # ЭТАП 1 — слово + ассоциация
        # -------------------------------------------------

        if stage == 1:

            for i in range(3):

                with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
                    gTTS(
                        text=english,
                        lang="en",
                        slow=True
                    ).save(f.name)

                    en_audio = AudioSegment.from_mp3(f.name)

                result += en_audio
                result += pause_short

                with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
                    gTTS(
                        text=russian,
                        lang="ru",
                        slow=True
                    ).save(f.name)

                    ru_audio = AudioSegment.from_mp3(f.name)

                result += ru_audio
                result += pause_long

        # -------------------------------------------------
        # ЭТАПЫ 2–5 — интенсивное повторение
        # -------------------------------------------------

        else:

            for i in range(10):

                with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
                    gTTS(
                        text=english,
                        lang="en",
                        slow=True
                    ).save(f.name)

                    en_audio = AudioSegment.from_mp3(f.name)

                result += en_audio
                result += pause_short

                with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
                    gTTS(
                        text=russian,
                        lang="ru",
                        slow=True
                    ).save(f.name)

                    ru_audio = AudioSegment.from_mp3(f.name)

                result += ru_audio
                result += pause_long

    filename = f"lesson_stage_{stage}.mp3"

    result.export(filename, format="mp3")

    return filename


# =========================================================
# ОТПРАВКА АУДИО
# =========================================================

def send_audio(chat_id, stage):

    filename = make_audio(stage)

    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"

    with open(filename, "rb") as audio:

        requests.post(
            url,
            data={
                "chat_id": chat_id,
                "caption": (
                    f"🎧 English Radar — этап {stage}\n\n"
                    "ROAD • SLIPPERY • DELAY\n"
                    "Медленное произношение\n"
                    "Повторение ×10"
                )
            },
            files={
                "audio": (
                    filename,
                    audio,
                    "audio/mpeg"
                )
            }
        )


# =========================================================
# ТЕКСТ УРОКА
# =========================================================

def lesson_text(stage):

    if stage == 1:

        return (
            "🇬🇧 ENGLISH RADAR\n\n"
            "🎓 Урок 1 — Дорога\n\n"

            "🔊 ROAD\n"
            "дорога\n"
            "💡 Представь дорогу перед собой.\n\n"

            "🔊 SLIPPERY\n"
            "скользкий\n"
            "💡 Представь скользкую дорогу после дождя.\n\n"

            "🔊 DELAY\n"
            "задержка\n"
            "💡 Представь грузовик, который задержался.\n\n"

            "🎧 Сейчас слушаем и повторяем.\n"
            "Не просто слушай — попробуй вспомнить."
        )

    if stage == 2:

        return (
            "🇬🇧 ENGLISH RADAR\n\n"
            "🔁 Этап 2 — соединяем слова\n\n"

            "ROAD — дорога\n"
            "SLIPPERY ROAD — скользкая дорога\n\n"

            "DELAY — задержка\n"
            "TRAFFIC DELAY — задержка движения\n\n"

            "🎧 Слушаем несколько раз."
        )

    if stage == 3:

        return (
            "🇬🇧 ENGLISH RADAR\n\n"
            "🔁 Этап 3 — вспоминаем\n\n"

            "ROAD — дорога\n"
            "SLIPPERY — скользкий\n"
            "DELAY — задержка\n\n"

            "Попробуй сказать английское слово,\n"
            "не подсматривая перевод."
        )

    if stage == 4:

        return (
            "🇬🇧 ENGLISH RADAR\n\n"
            "🔁 Этап 4 — строим маленькие фразы\n\n"

            "SLIPPERY ROAD — скользкая дорога\n\n"
            "TRAFFIC DELAY — задержка движения\n\n"

            "🎧 Слушаем и повторяем."
        )

    return (
        "🇬🇧 ENGLISH RADAR\n\n"
        "🏁 Этап 5 — закрепление\n\n"

        "ROAD — дорога\n"
        "SLIPPERY ROAD — скользкая дорога\n"
        "TRAFFIC DELAY — задержка движения\n\n"

        "Теперь попробуй вспомнить всё без подсказки.\n\n"
        "🧠 Ошибся — отлично. Значит, нашли границу памяти."
    )


# =========================================================
# ОПРЕДЕЛЯЕМ ЭТАП ПО ВРЕМЕНИ КИЕВА
# =========================================================

def current_stage():

    now = datetime.now(
        ZoneInfo("Europe/Kyiv")
    )

    hour = now.hour

    stages = {
        8: 1,
        10: 2,
        12: 3,
        14: 4,
        16: 5
    }

    return stages.get(hour)


# =========================================================
# ПОЛУЧАЕМ TELEGRAM
# =========================================================

updates = telegram("getUpdates")


for update in updates.get("result", []):

    message = update.get("message")

    if not message:
        continue

    chat_id = message["chat"]["id"]

    text = message.get("text", "").strip().lower()

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    if text.startswith("/start"):

        telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": (
                    "🇬🇧 ENGLISH RADAR\n\n"
                    "Бот подключён.\n\n"
                    "📚 Каждый день будет 5 этапов:\n"
                    "08:00\n"
                    "10:00\n"
                    "12:00\n"
                    "14:00\n"
                    "16:00\n\n"
                    "🎧 Каждый урок сопровождается аудио.\n\n"
                    "Для немедленной проверки напиши:\n"
                    "/test"
                )
            }
        )

    # -----------------------------------------------------
    # TEST — ЗАПУСК ПРЯМО СЕЙЧАС
    # -----------------------------------------------------

    elif text == "/test":

        stage = 1

        telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": lesson_text(stage)
            }
        )

        send_audio(chat_id, stage)

    # -----------------------------------------------------
    # АВТОМАТИЧЕСКИЙ УРОК
    # -----------------------------------------------------

    stage = current_stage()

    if stage:

        telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": lesson_text(stage)
            }
        )

        send_audio(chat_id, stage)


print("English Radar работает.")
