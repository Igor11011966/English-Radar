import os
import json
import asyncio
import urllib.request
import urllib.parse
import requests
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

import edge_tts
from pydub import AudioSegment


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()

KYIV = ZoneInfo("Europe/Kyiv")

CHAT_FILE = "chat_id.txt"


# ==================================================
# TELEGRAM
# ==================================================

def telegram(method, data=None):

    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if data:
        data = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


# ==================================================
# СОХРАНЯЕМ CHAT ID
# ==================================================

def save_chat_id(chat_id):

    with open(CHAT_FILE, "w") as file:
        file.write(str(chat_id))


def get_chat_id():

    if os.path.exists(CHAT_FILE):

        with open(CHAT_FILE, "r") as file:
            value = file.read().strip()

            if value:
                return value

    return None


# ==================================================
# АССОЦИАЦИИ
# ==================================================

WORDS = [

    {
        "english": "ROAD",
        "russian": "дорога",
        "association": (
            "Представь дорогу прямо перед собой. "
            "Ты едешь по дороге на грузовике."
        )
    },

    {
        "english": "SLIPPERY",
        "russian": "скользкий",
        "association": (
            "Представь мокрую дорогу. "
            "Она скользкая, и грузовик начинает немного заносить."
        )
    },

    {
        "english": "DELAY",
        "russian": "задержка",
        "association": (
            "Представь грузовик перед портом. "
            "Очередь стоит, и погрузка задерживается."
        )
    }
]


# ==================================================
# ГОЛОС
# ==================================================

ENGLISH_VOICE = "en-US-JennyNeural"
RUSSIAN_VOICE = "ru-RU-SvetlanaNeural"


async def create_voice(text, voice, rate="-20%"):

    filename = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    ).name

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate
    )

    await communicate.save(filename)

    audio = AudioSegment.from_file(filename)

    os.remove(filename)

    return audio


# ==================================================
# АУДИО
# ==================================================

async def make_audio():

    result = AudioSegment.empty()

    pause_1 = AudioSegment.silent(duration=1200)
    pause_2 = AudioSegment.silent(duration=1800)
    pause_recall = AudioSegment.silent(duration=3500)

    for word in WORDS:

        english = word["english"]
        russian = word["russian"]
        association = word["association"]

        # ------------------------------------------
        # ЗНАКОМСТВО
        # ------------------------------------------

        result += await create_voice(
            english,
            ENGLISH_VOICE,
            "-20%"
        )

        result += pause_1

        result += await create_voice(
            association,
            RUSSIAN_VOICE,
            "-15%"
        )

        result += pause_2

        result += await create_voice(
            english,
            ENGLISH_VOICE,
            "-20%"
        )

        result += pause_1

        result += await create_voice(
            russian,
            RUSSIAN_VOICE,
            "-15%"
        )

        result += pause_2

        # ------------------------------------------
        # 10 ПОВТОРЕНИЙ
        # ------------------------------------------

        english_audio = await create_voice(
            english,
            ENGLISH_VOICE,
            "-20%"
        )

        russian_audio = await create_voice(
            russian,
            RUSSIAN_VOICE,
            "-15%"
        )

        for i in range(10):

            result += english_audio

            result += pause_1

            # Первые 6 раз слышим перевод
            if i < 6:

                result += russian_audio

                result += pause_1

            # Последние 4 раза пробуем вспомнить
            else:

                result += pause_1

                result += russian_audio

                result += pause_1

    # ==================================================
    # RECALL
    # ==================================================

    result += await create_voice(
        "Теперь попробуй вспомнить сам.",
        RUSSIAN_VOICE,
        "-15%"
    )

    result += pause_2

    for word in WORDS:

        result += await create_voice(
            word["russian"],
            RUSSIAN_VOICE,
            "-15%"
        )

        # МЕСТО ДЛЯ ВСПОМИНАНИЯ
        result += pause_recall

        result += await create_voice(
            word["english"],
            ENGLISH_VOICE,
            "-20%"
        )

        result += pause_2

    # ==================================================
    # ПОСЛЕДНЯЯ ПРОВЕРКА
    # ==================================================

    result += await create_voice(
        "Последний раз. Попробуй сказать сам.",
        RUSSIAN_VOICE,
        "-15%"
    )

    result += pause_2

    for word in WORDS:

        result += await create_voice(
            word["english"],
            ENGLISH_VOICE,
            "-20%"
        )

        result += pause_1

    result.export(
        "lesson.mp3",
        format="mp3",
        bitrate="128k"
    )


# ==================================================
# ОТПРАВКА АУДИО
# ==================================================

def send_audio(chat_id):

    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"

    with open("lesson.mp3", "rb") as audio:

        response = requests.post(

            url,

            data={
                "chat_id": chat_id,

                "caption": (
                    "🎧 ENGLISH RADAR — УРОК 1\n\n"
                    "🛣 ROAD — дорога\n"
                    "🌧 SLIPPERY — скользкий\n"
                    "🚛 DELAY — задержка\n\n"
                    "🧠 Ассоциации\n"
                    "🔁 10 повторений каждого слова\n"
                    "🎯 Recall — вспоминаем без подсказки\n\n"
                    "Скорость речи: немного медленнее обычной."
                )
            },

            files={
                "audio": (
                    "lesson.mp3",
                    audio,
                    "audio/mpeg"
                )
            }
        )

    print(response.text)


# ==================================================
# ТЕКСТОВЫЙ УРОК
# ==================================================

def send_text_lesson(chat_id):

    text = (
        "🇬🇧 ENGLISH RADAR\n\n"
        "🎓 УРОК 1 — ДОРОГА\n\n"

        "🛣 ROAD — дорога\n"
        "🌧 SLIPPERY — скользкий\n"
        "🚛 DELAY — задержка\n\n"

        "Сначала создаём образ в голове.\n"
        "Потом слушаем и повторяем.\n"
        "В конце — проверяем память.\n\n"

        "🎧 Аудио ниже."
    )

    telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text
        }
    )


# ==================================================
# ОБРАБОТКА /START
# ==================================================

def check_start():

    updates = telegram("getUpdates")

    for update in updates.get("result", []):

        message = update.get("message")

        if not message:
            continue

        chat_id = message["chat"]["id"]

        save_chat_id(chat_id)

        text = message.get("text", "")

        if text.startswith("/start"):

            telegram(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "🇬🇧 ENGLISH RADAR\n\n"
                        "Бот подключён.\n"
                        "Твой Telegram сохранён.\n\n"
                        "Теперь я могу присылать уроки автоматически."
                    )
                }
            )


# ==================================================
# ОСНОВНАЯ ПРОГРАММА
# ==================================================

def main():

    # Проверяем Telegram
    check_start()

    chat_id = get_chat_id()

    if not chat_id:

        print("CHAT ID пока не найден.")

        return

    now = datetime.now(KYIV)

    print(
        "Kyiv time:",
        now.strftime("%Y-%m-%d %H:%M")
    )

    hour = now.hour

    # Пока тестируем только ручной запуск
    # и утренний урок в 08:00.

    if hour == 8 or os.environ.get("TEST_LESSON") == "1":

        print("Запускаем урок.")

        send_text_lesson(chat_id)

        asyncio.run(
            make_audio()
        )

        send_audio(chat_id)

        print("Урок отправлен.")

    else:

        print(
            "Сейчас не время урока.",
            hour
        )


main()
