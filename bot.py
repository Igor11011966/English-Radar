import os
import json
import asyncio
import requests
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
        data=data or {},
        timeout=30
    )

    print(method, ":", response.text)

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(result)

    return result


def load_words():
    with open(
        WORDS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        words = json.load(f)

    if not isinstance(words, list):
        raise ValueError(
            "words.json должен содержать список"
        )

    return words


def get_today_words():

    words = load_words()

    today = datetime.now(KYIV).date()

    day_number = (
        today - START_DATE
    ).days

    if day_number < 0:
        day_number = 0

    start = day_number * 3
    end = start + 3

    today_words = words[start:end]

    if len(today_words) < 3:

        raise ValueError(
            "В библиотеке закончились слова"
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

        "ROAD":
            "The road is long.",

        "SLIPPERY":
            "The road is slippery.",

        "DELAY":
            "There is a delay.",

        "TRUCK":
            "The truck is big.",

        "DRIVER":
            "The driver is tired.",

        "STOP":
            "Stop the truck.",

        "TURN":
            "Turn right.",

        "FAST":
            "The truck is fast.",

        "SLOW":
            "Drive slow.",

        "FUEL":
            "We need fuel.",

        "TRAFFIC":
            "There is traffic.",

        "BRAKE":
            "Press the brake.",

        "LEFT":
            "Turn left.",

        "RIGHT":
            "Turn right.",

        "RAIN":
            "It is raining.",

        "SNOW":
            "It is snowing.",

        "WAIT":
            "Wait here.",

        "ARRIVE":
            "We arrive tomorrow."
    }

    return sentences.get(
        word,
        word
    )


async def make_voice(
    text,
    filename,
    voice="en-US-GuyNeural"
):

    command = [
        "edge-tts",
        "--voice",
        voice,
        "--rate",
        "-10%",
        "--text",
        text,
        "--write-media",
        filename
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:

        error = stderr.decode(
            errors="ignore"
        )

        print(error)

        raise RuntimeError(
            "Ошибка edge-tts"
        )


def make_audio(words, stage):

    filename = "lesson.mp3"

    if stage == 1:

        parts = []

        for item in words:

            parts.append(
                item["word"]
            )

            parts.append(
                item["association"]
            )

            parts.append(
                item["translation"]
            )

            for _ in range(10):

                parts.append(
                    item["word"]
                )

                parts.append(
                    item["translation"]
                )

        text = ". ".join(parts)

    elif stage == 2:

        parts = []

        for item in words:

            sentence = make_sentence(
                item["word"]
            )

            for _ in range(5):

                parts.append(
                    item["word"]
                )

                parts.append(
                    item["translation"]
                )

                parts.append(
                    sentence
                )

        text = ". ".join(parts)

    elif stage == 3:

        parts = [
            "Recall.",
            "Listen carefully.",
            "Try to remember the meaning."
        ]

        for item in words:

            for _ in range(5):

                parts.append(
                    item["word"]
                )

            parts.append(
                item["translation"]
            )

        text = " ".join(parts)

    elif stage == 4:

        parts = [
            "Creative repetition."
        ]

        for item in words:

            sentence = make_sentence(
                item["word"]
            )

            for _ in range(5):

                parts.append(
                    sentence
                )

                parts.append(
                    item["word"]
                )

        text = " ".join(parts)

    else:

        parts = [
            "Final test."
        ]

        for item in words:

            for _ in range(5):

                parts.append(
                    item["word"]
                )

            parts.append(
                item["translation"]
            )

        text = " ".join(parts)

    asyncio.run(
        make_voice(
            text,
            filename
        )
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

    elif stage == 2:

        title = "🔄 ПОВТОРЕНИЕ №2"

        body = ""

        for item in words:

            body += (
                f"\n{item['word']}\n"
                f"👉 {make_sentence(item['word'])}\n"
            )

    elif stage == 3:

        title = "🧠 RECALL"

        body = (
            "\nСначала услышь слово."
            "\nПопробуй вспомнить перевод."
        )

    elif stage == 4:

        title = "🔄 ТВОРЧЕСКОЕ ПОВТОРЕНИЕ"

        body = (
            "\nСлушай фразы."
            "\nУзнавай знакомые слова."
        )

    else:

        title = "🎓 ФИНАЛЬНАЯ ПРОВЕРКА"

        body = (
            "\nПопробуй вспомнить"
            "\nвсе три слова самостоятельно."
        )

    telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text":
                "🇬🇧 ENGLISH RADAR\n\n"
                + title
                + "\n"
                + body
        }
    )


def send_audio(filename, stage):

    captions = {

        1:
            "🎧 Новые слова + ассоциации + ×10",

        2:
            "🎧 Повторение №2",

        3:
            "🎧 RECALL",

        4:
            "🎧 Творческое повторение",

        5:
            "🎧 Финальная проверка"
    }

    url = (
        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendAudio"
    )

    with open(
        filename,
        "rb"
    ) as audio:

        response = requests.post(

            url,

            data={
                "chat_id": CHAT_ID,
                "caption":
                    captions[stage]
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

    print(
        "AUDIO:",
        response.text
    )

    response.raise_for_status()


def main():

    print(
        "=== ENGLISH RADAR ==="
    )

    print(
        "Kyiv:",
        datetime.now(
            KYIV
        ).strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    words = get_today_words()

    stage = get_stage()

    print(
        "Stage:",
        stage
    )

    print(
        "Words:",
        [
            item["word"]
            for item in words
        ]
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
        "=== SUCCESS ==="
    )


if __name__ == "__main__":
    main()
