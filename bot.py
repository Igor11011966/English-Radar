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

PROGRESS_FILE = "progress.json"


# --------------------------------------------------
# TELEGRAM
# --------------------------------------------------

def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if data:
        data = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


# --------------------------------------------------
# ПАМЯТЬ ПРОГРАММЫ
# --------------------------------------------------

def load_progress():

    if not os.path.exists(PROGRESS_FILE):

        return {
            "chat_id": None,
            "day": 1,
            "words": [],
            "learned": [],
            "date": ""
        }

    with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_progress(progress):

    with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            progress,
            file,
            ensure_ascii=False,
            indent=2
        )


# --------------------------------------------------
# НАШИ ПЕРВЫЕ СЛОВА
# --------------------------------------------------

WORD_BASE = [

    ("ROAD", "дорога"),
    ("WET", "мокрый"),
    ("TRUCK", "грузовик"),

    ("CAR", "машина"),
    ("DRIVE", "ехать / водить"),
    ("STOP", "остановиться"),
    ("GO", "ехать / идти"),
    ("TURN", "поворачивать"),
    ("LEFT", "налево / левый"),
    ("RIGHT", "направо / правый"),

    ("STRAIGHT", "прямо"),
    ("FAST", "быстро"),
    ("SLOW", "медленно"),
    ("NEAR", "близко"),
    ("FAR", "далеко"),

    ("BRIDGE", "мост"),
    ("EXIT", "выезд"),
    ("ENTRANCE", "въезд"),

    ("LOAD", "груз / загружать"),
    ("UNLOAD", "разгружать"),

    ("CONTAINER", "контейнер"),
    ("TRAILER", "прицеп"),
    ("DRIVER", "водитель"),
    ("PORT", "порт"),

    ("SHIP", "судно"),
    ("WEIGHT", "вес"),
    ("DOCUMENT", "документ"),
    ("CHECK", "проверять"),
    ("WAIT", "ждать"),
    ("READY", "готов"),

]


# --------------------------------------------------
# ПОЛУЧАЕМ НОВЫЕ 3 СЛОВА
# --------------------------------------------------

def get_new_words(progress):

    used = progress.get("learned", [])

    available = []

    for word, translation in WORD_BASE:

        if word not in used:
            available.append((word, translation))

    return available[:3]


# --------------------------------------------------
# АУДИО
# --------------------------------------------------

def make_audio(words, filename="lesson.mp3"):

    result = AudioSegment.empty()

    pause_english = AudioSegment.silent(duration=1200)
    pause_russian = AudioSegment.silent(duration=1800)

    for english, russian in words:

        for _ in range(10):

            with tempfile.NamedTemporaryFile(
                suffix=".mp3"
            ) as en_file:

                gTTS(
                    text=english,
                    lang="en",
                    slow=True
                ).save(en_file.name)

                english_audio = AudioSegment.from_mp3(
                    en_file.name
                )

            with tempfile.NamedTemporaryFile(
                suffix=".mp3"
            ) as ru_file:

                gTTS(
                    text=russian,
                    lang="ru",
                    slow=True
                ).save(ru_file.name)

                russian_audio = AudioSegment.from_mp3(
                    ru_file.name
                )

            result += english_audio
            result += pause_english

            result += russian_audio
            result += pause_russian

    result.export(
        filename,
        format="mp3"
    )

    return filename


# --------------------------------------------------
# ОТПРАВКА ТЕКСТА
# --------------------------------------------------

def send_message(chat_id, text):

    telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text
        }
    )


# --------------------------------------------------
# ОТПРАВКА АУДИО
# --------------------------------------------------

def send_audio(chat_id, filename, caption):

    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"

    with open(filename, "rb") as audio:

        response = requests.post(

            url,

            data={
                "chat_id": chat_id,
                "caption": caption
            },

            files={
                "audio": (
                    filename,
                    audio,
                    "audio/mpeg"
                )
            }
        )

    print(response.text)


# --------------------------------------------------
# 08:00 — НОВЫЕ СЛОВА
# --------------------------------------------------

def run_lesson(progress):

    now = datetime.now(ZoneInfo("Europe/Kyiv"))
    hour = now.hour

    print("Kyiv time:", now.strftime("%Y-%m-%d %H:%M:%S"))

    if hour == 8:
        lesson_morning(progress)

    elif hour == 10:
        lesson_combinations(progress)

    elif hour == 12:
        lesson_sentence(progress)

    elif hour == 14:
        lesson_recall(progress)

    elif hour == 16:
        lesson_explain(progress)

    else:
        print("Сейчас учебного этапа нет.")

    if not words:
        return

    progress["words"] = words

    for word, _ in words:

        if word not in progress["learned"]:
            progress["learned"].append(word)

    save_progress(progress)

    text = (
        "🇬🇧 ENGLISH RADAR\n\n"
        f"🎓 День {progress['day']} — новые слова\n\n"
    )

    for word, translation in words:

        text += f"🔹 {word} — {translation}\n"

    text += (
        "\n🎧 Сейчас слушаем.\n"
        "Каждое слово будет повторено 10 раз.\n\n"
        "Главное правило:\n"
        "не просто услышать — попытайся вспомнить."
    )

    send_message(
        progress["chat_id"],
        text
    )

    filename = make_audio(
        words,
        "lesson.mp3"
    )

    send_audio(
        progress["chat_id"],
        filename,
        "🎧 English Radar — повторение ×10"
    )


# --------------------------------------------------
# 10:00 — СОЧЕТАНИЯ
# --------------------------------------------------

def lesson_combinations(progress):

    words = progress.get("words", [])

    if not words:
        return

    first = words[0]
    second = words[1]

    text = (
        "🇬🇧 ENGLISH RADAR\n\n"
        "🔄 Повторяем и соединяем слова\n\n"
        f"{first[0]} — {first[1]}\n"
        f"{second[0]} — {second[1]}\n\n"
        f"👉 {second[0]} {first[0]}\n"
        f"   {second[1]} {first[1]}\n\n"
        "Теперь попробуй сам вспомнить английский вариант."
    )

    send_message(
        progress["chat_id"],
        text
    )


# --------------------------------------------------
# 12:00 — ПРОСТАЯ ФРАЗА
# --------------------------------------------------

def lesson_sentence(progress):

    words = progress.get("words", [])

    if len(words) < 2:
        return

    first = words[0]
    second = words[1]

    text = (
        "🇬🇧 ENGLISH RADAR\n\n"
        "🧩 Строим простую фразу\n\n"
        "THE ROAD IS WET.\n\n"
        "Дорога мокрая.\n\n"
        "Объясни это семилетнему ребёнку:\n"
        "что означает ROAD?\n"
        "что означает WET?\n\n"
        "Не смотри подсказку — сначала вспомни."
    )

    send_message(
        progress["chat_id"],
        text
    )


# --------------------------------------------------
# 14:00 — RECALL
# --------------------------------------------------

def lesson_recall(progress):

    words = progress.get("words", [])

    if not words:
        return

    text = (
        "🧠 ENGLISH RADAR — RECALL\n\n"
        "Теперь без подсказки.\n\n"
    )

    for _, translation in words:

        text += f"❓ Как будет: {translation}?\n\n"

    text += (
        "Пауза.\n"
        "Попробуй вспомнить вслух.\n\n"
        "ROAD\n"
        "WET\n"
        "TRUCK"
    )

    send_message(
        progress["chat_id"],
        text
    )


# --------------------------------------------------
# 16:00 — ОБЪЯСНЕНИЕ
# --------------------------------------------------

def lesson_explain(progress):

    words = progress.get("words", [])

    if not words:
        return

    text = (
        "🗣️ ENGLISH RADAR — ОБЪЯСНИ\n\n"
        "Представь, что перед тобой семилетний ребёнок.\n\n"
        "Объясни ему простыми словами:\n\n"
        f"ROAD — {words[0][1]}\n"
        f"WET — {words[1][1]}\n"
        f"TRUCK — {words[2][1]}\n\n"
        "Если можешь объяснить просто — значит,\n"
        "ты начинаешь действительно понимать.\n\n"
        "Ошибки — это нормально.\n"
        "Они показывают, где память ещё работает."
    )

    send_message(
        progress["chat_id"],
        text
    )


# --------------------------------------------------
# ОПРЕДЕЛЯЕМ ЭТАП ПО ЧАСУ
# --------------------------------------------------

def run_lesson(progress):

    hour = datetime.now().hour

    print("Current hour:", hour)

    if hour == 8:

        lesson_morning(progress)

    elif hour == 10:

        lesson_combinations(progress)

    elif hour == 12:

        lesson_sentence(progress)

    elif hour == 14:

        lesson_recall(progress)

    elif hour == 16:

        lesson_explain(progress)

    else:

        print("Сейчас учебного этапа нет.")


# --------------------------------------------------
# START
# --------------------------------------------------

progress = load_progress()

updates = telegram("getUpdates")

for update in updates.get("result", []):

    message = update.get("message")

    if not message:
        continue

    chat_id = message["chat"]["id"]

    progress["chat_id"] = chat_id

    text = message.get("text", "")

    if text.startswith("/start"):

        send_message(
            chat_id,
            (
                "🇬🇧 ENGLISH RADAR\n\n"
                "Бот подключён.\n"
                "Твой Telegram сохранён.\n\n"
                "Теперь я могу присылать уроки автоматически."
            )
        )

        save_progress(progress)


# Если chat_id уже известен —
# запускаем нужный этап.

if progress.get("chat_id"):

    run_lesson(progress)

else:

    print(
        "Chat ID пока неизвестен. "
        "Отправь боту /start."
    )
