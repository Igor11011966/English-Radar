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

KYIV = ZoneInfo("Europe/Kyiv")

WORDS_FILE = "words.json"


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if data:
        data = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def get_chat_id():

    updates = telegram("getUpdates")

    latest_chat_id = None

    for update in updates.get("result", []):

        message = update.get("message")

        if not message:
            continue

        latest_chat_id = message["chat"]["id"]

    return latest_chat_id


def load_words():

    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_today_words():

    words = load_words()

    start_date = datetime(2026, 8, 17, tzinfo=KYIV)

    now = datetime.now(KYIV)

    day_number = (now.date() - start_date.date()).days

    if day_number < 0:
        day_number = 0

    start_index = day_number * 3

    today_words = words[start_index:start_index + 3]

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

    await process.communicate()


def make_audio(words, stage):

    filename = "lesson.mp3"

    parts = []

    if stage == 1:

        for item in words:

            parts.append(
                f"{item['word']}. "
                f"{item['association']} "
                f"{item['translation']}. "
            )

            for _ in range(10):

                parts.append(
                    f"{item['word']}. "
                    f"{item['translation']}. "
                )

    elif stage == 2:

        for item in words:

            sentence = make_sentence(item["word"])

            parts.append(
                f"{item['word']}. "
                f"{item['translation']}. "
                f"{sentence}. "
            )

            for _ in range(5):

                parts.append(
                    f"{item['word']}. "
                    f"{sentence}. "
                )

    elif stage == 3:

        parts.append(
            "Теперь вспоминаем. "
            "Сначала слушай английское слово. "
            "Попробуй вспомнить перевод сам."
        )

        for item in words:

            for _ in range(5):

                parts.append(
                    f"{item['word']}."
                )

                parts.append(
                    f"{item['translation']}."
                )

    elif stage == 4:

        for item in words:

            sentence = make_sentence(item["word"])

            parts.append(
                f"{sentence}. "
                f"{item['word']}. "
                f"{item['translation']}."
            )

            for _ in range(5):

                parts.append(
                    f"{sentence}. "
                    f"{item['word']}."
                )

    else:

        parts.append(
            "Финальная проверка. "
            "Не спеши. Вспоминай сам."
        )

        for item in words:

            for _ in range(5):

                parts.append(
                    f"{item['word']}."
                )

            parts.append(
                f"{item['translation']}."
            )

    text = " ".join(parts)

    asyncio.run(
        make_voice(
            text,
            filename,
            "en-US-GuyNeural",
            "-15%"
        )
    )

    return filename


def make_sentence(word):

    sentences = {

        "ROAD": "The road is long",

        "SLIPPERY": "The road is slippery",

        "DELAY": "There is a delay",

        "TRUCK": "The truck is big",

        "DRIVER": "The driver is tired",

        "STOP": "Stop the truck",

        "TURN": "Turn right",

        "FAST": "The truck is fast",

        "SLOW": "Drive slow",

        "FUEL": "We need fuel",

        "ROADWORK": "There is roadwork",

        "TRAFFIC": "There is traffic",

        "BRAKE": "Press the brake",

        "LEFT": "Turn left",

        "RIGHT": "Turn right",

        "MORNING": "Good morning",

        "NIGHT": "Good night",

        "RAIN": "It is raining",

        "SNOW": "It is snowing",

        "WAIT": "Wait here",

        "ARRIVE": "We arrive tomorrow"
    }

    return sentences.get(word, word)


def send_text(chat_id, words, stage):

    if stage == 1:

        title = "🌅 Урок начинается"

        body = ""

        for item in words:

            body += (
                f"\n🔊 {item['word']}\n"
                f"🇷🇺 {item['translation']}\n"
                f"🧠 {item['association']}\n"
            )

        body += "\n🎧 Слушай аудио и не спеши."

    elif stage == 2:

        title = "🔄 Повторение №2"

        body = "\n"

        for item in words:

            body += (
                f"{item['word']} — {make_sentence(item['word'])}\n"
            )

    elif stage == 3:

        title = "🧠 RECALL — вспоминаем"

        body = (
            "\nСначала услышь слово.\n"
            "Попробуй вспомнить перевод ДО того, "
            "как услышишь ответ."
        )

    elif stage == 4:

        title = "🔄 Творческое повторение"

        body = (
            "\nСегодня смотрим на слова с другой стороны.\n"
            "Слушай фразы и узнавай знакомые слова."
        )

    else:

        title = "🎓 Финальная проверка"

        body = (
            "\nПоследний проход.\n"
            "Попробуй вспомнить значение каждого слова самостоятельно."
        )

    telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": (
                "🇬🇧 ENGLISH RADAR\n\n"
                f"{title}\n"
                f"{body}"
            )
        }
    )


def send_audio(chat_id, filename, stage):

    captions = {
        1: "🎧 Урок 1 — знакомство + ассоциации + повторение ×10",
        2: "🎧 Повторение №2 — слова в простых фразах",
        3: "🎧 RECALL — сначала вспоминаем сами",
        4: "🎧 Творческое повторение",
        5: "🎧 Финальная проверка"
    }

    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"

    with open(filename, "rb") as audio:

        requests.post(
            url,
            data={
                "chat_id": chat_id,
                "caption": captions.get(stage, "🎧 English Radar")
            },
            files={
                "audio": (
                    filename,
                    audio,
                    "audio/mpeg"
                )
            }
        )


def main():

    now = datetime.now(KYIV)

    print("Kyiv time:", now.strftime("%Y-%m-%d %H:%M"))

    chat_id = get_chat_id()

    if not chat_id:

        print("Chat ID не найден.")

        return

    words = get_today_words()

    if not words:

        print("Библиотека слов закончилась.")

        return

    stage = get_stage()

    print("Stage:", stage)

    print(
        "Today's words:",
        [item["word"] for item in words]
    )

    send_text(
        chat_id,
        words,
        stage
    )

    filename = make_audio(
        words,
        stage
    )

    send_audio(
        chat_id,
        filename,
        stage

    )

    print("English Radar успешно отправил урок.")


if __name__ == "__main__":
    main()
