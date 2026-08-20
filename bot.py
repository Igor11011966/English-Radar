import os
import json
import urllib.request
import urllib.parse
import requests
import asyncio
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

KYIV = ZoneInfo("Europe/Kyiv")

WORDS_FILE = "words.json"
START_DATE = datetime(2026, 8, 17, tzinfo=KYIV).date()


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    response = requests.post(
        url,
        data=data,
        timeout=30
    )

    print("TELEGRAM RESPONSE:")
    print(response.text)

    response.raise_for_status()

    return response.json()    


def load_words():
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
       return json. load(f)


def get_today_words():
    words = load_words()

    today = datetime.now(KYIV).date()

    day_number = (today - START_DATE).days

    if day_number < 0:
        day_number = 0

    start_index = day_number * 3
    today_words = words[start_index:start_index + 3]

    if len(today_words) < 3:
        raise ValueError(
            f"Для дня {day_number + 1} недостаточно слов в библиотеке"
        )

    return today_words


def get_stage():
    hour = datetime.now(KYIV).hour

    if hour < 9:
        return 1

    if hour < 11:
        return 2

    if hour < 13:
        return 3

    if hour < 15:
        return 4

    return 5


def make_sentence(word):
    sentences = {
        "ROAD": "The road is long.",
        "SLIPPERY": "The road is slippery.",
        "DELAY": "There is a delay.",
        "TRUCK": "The truck is big.",
        "DRIVER": "The driver is tired.",
        "STOP": "Stop the truck.",
        "TURN": "Turn right.",
        "FAST": "The truck is fast.",
        "SLOW": "Drive slow.",
        "FUEL": "We need fuel.",
        "ROADWORK": "There is roadwork.",
        "TRAFFIC": "There is traffic.",
        "BRAKE": "Press the brake.",
        "LEFT": "Turn left.",
        "RIGHT": "Turn right.",
        "MORNING": "Good morning.",
        "NIGHT": "Good night.",
        "RAIN": "It is raining.",
        "SNOW": "It is snowing.",
        "WAIT": "Wait here.",
        "ARRIVE": "We arrive tomorrow."
    }

    return sentences.get(word, word)


async def make_voice(text, filename, voice, rate="-15%"):
    command = [
        "edge-tts",
        "--voice",
        voice,
        "--rate",
        rate,
        "--text",
        text,
        "--write-media",
        filename
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print(stderr.decode(errors="ignore"))
        raise RuntimeError("Ошибка edge-tts")


def run_voice(text, filename, voice):
    asyncio.run(
        make_voice(
            text,
            filename,
            voice,
            "-15%"
        )
    )


def make_audio(words, stage):

    filename = "lesson.mp3"

    # Создаём текст для аудио.
    # Английский и русский будут озвучиваться
    # разными естественными голосами.

    parts = []

    if stage == 1:

        for item in words:

            parts.append({
                "en": item["word"],
                "ru": item["translation"]
            })

            parts.append({
                "en": item["association"],
                "ru": item["translation"]
            })

            for _ in range(10):

                parts.append({
                    "en": item["word"],
                    "ru": item["translation"]
                })

    elif stage == 2:

        for item in words:

            sentence = make_sentence(item["word"])

            for _ in range(5):

                parts.append({
                    "en": item["word"],
                    "ru": item["translation"]
                })

                parts.append({
                    "en": sentence,
                    "ru": item["translation"]
                })

    elif stage == 3:

        for item in words:

            for _ in range(5):

                parts.append({
                    "en": item["word"],
                    "ru": ""
                })

                parts.append({
                    "en": "",
                    "ru": item["translation"]
                })

    elif stage == 4:

        for item in words:

            sentence = make_sentence(item["word"])

            for _ in range(5):

                parts.append({
                    "en": sentence,
                    "ru": item["translation"]
                })

                parts.append({
                    "en": item["word"],
                    "ru": item["translation"]
                })

    else:

        for item in words:

            for _ in range(5):

                parts.append({
                    "en": item["word"],
                    "ru": ""
                })

            parts.append({
                "en": "",
                "ru": item["translation"]
            })

    # Генерируем отдельные кусочки.
    # Это позволяет английскому и русскому иметь
    # нормальное собственное произношение.

    files = []

    for index, part in enumerate(parts):

        en = part["en"]
        ru = part["ru"]

        if en:

            en_file = f"en_{index}.mp3"

            run_voice(
                en,
                en_file,
                "en-US-GuyNeural"
            )

            files.append(en_file)

        if ru:

            ru_file = f"ru_{index}.mp3"

            run_voice(
                ru,
                ru_file,
                "ru-RU-DmitryNeural"
            )

            files.append(ru_file)

    # Склеиваем аудио через ffmpeg

    list_file = "audio_list.txt"

    with open(list_file, "w", encoding="utf-8") as f:

        for audio_file in files:
            absolute = os.path.abspath(audio_file)
            f.write(
                f"file '{absolute}'\n"
            )

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_file,
        "-c",
        "copy",
        filename
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print(result.stderr)

        raise RuntimeError(
            "Ошибка объединения аудио"
        )

    return filename


def send_text(words, stage):

    if stage == 1:

        title = "🌅 НОВЫЕ СЛОВА"

        body = ""

        for item in words:

            body += (
                f"\n🔊 {item['word']}\n"
                f"🇷🇺 {item['translation']}\n"
                f"🧠 {item['association']}\n"
            )

        body += "\n🎧 Сначала представь картинку. Потом слушай."

    elif stage == 2:

        title = "🔄 ПОВТОРЕНИЕ №2"

        body = ""

        for item in words:

            body += (
                f"\n{item['word']}\n"
                f"👉 {make_sentence(item['word'])}\n"
                f"🇷🇺 {item['translation']}\n"
            )

    elif stage == 3:

        title = "🧠 RECALL"

        body = (
            "\nСначала услышь английское слово.\n"
            "Попробуй вспомнить перевод сам.\n"
            "Ответ появится после паузы."
        )

    elif stage == 4:

        title = "🔄 ТВОРЧЕСКОЕ ПОВТОРЕНИЕ"

        body = (
            "\nСмотрим на знакомые слова с другой стороны.\n"
            "Слушай фразы и узнавай слова."
        )

    else:

        title = "🎓 ФИНАЛЬНАЯ ПРОВЕРКА"

        body = (
            "\nНе подглядывай.\n"
            "Попробуй самостоятельно вспомнить все три слова."
        )

    telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": (
                "🇬🇧 ENGLISH RADAR\n\n"
                f"{title}\n"
                f"{body}"
            )
        }
    )


def send_audio(filename, stage):

    captions = {
        1: "🎧 Новые слова + ассоциации + 10 повторений",
        2: "🎧 Повторение №2 — простые фразы",
        3: "🎧 RECALL — вспоминаем самостоятельно",
        4: "🎧 Творческое повторение",
        5: "🎧 Финальная проверка"
    }

    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"

    with open(filename, "rb") as audio:

        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": captions[stage]
            },
            files={
                "audio": (
                    "lesson.mp3",
                    audio,
                    "audio/mpeg"
                )
            },
            timeout=120
        )

    print("Telegram:", response.text)

    if not response.ok:
        raise RuntimeError(
            "Telegram не принял аудио"
        )


def main():

    now = datetime.now(KYIV)

    print(
        "Kyiv time:",
        now.strftime("%Y-%m-%d %H:%M")
    )

    print(
        "Chat ID:",
        CHAT_ID[:4] + "***"
    )

    words = get_today_words()

    print(
        "Today's words:",
        [item["word"] for item in words]
    )

    stage = get_stage()

    print(
        "Stage:",
        stage
    )

    send_text(
        words,
        stage
    )

    filename = make_audio(
        words,
        stage
    )

    send_audio(
        filename,
        stage
    )

    print(
        "English Radar успешно завершил урок."
    )


if __name__ == "__main__":
    main()
