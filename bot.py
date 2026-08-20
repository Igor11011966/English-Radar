import os
import json
import requests
import asyncio
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

KYIV = ZoneInfo("Europe/Kyiv")

WORDS_FILE = "words.json"

# С этого дня начинается наша библиотека
START_DATE = datetime(2026, 8, 17, tzinfo=KYIV).date()


# ============================================================
# TELEGRAM
# ============================================================

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

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram error: {result}"
        )

    return result


# ============================================================
# БИБЛИОТЕКА СЛОВ
# ============================================================

def load_words():

    if not os.path.exists(WORDS_FILE):
        raise FileNotFoundError(
            f"Не найден файл {WORDS_FILE}"
        )

    with open(
        WORDS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        words = json.load(f)

    if not isinstance(words, list):
        raise ValueError(
            "words.json должен содержать список слов"
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

    start_index = day_number * 3

    today_words = words[
        start_index:start_index + 3
    ]

    if len(today_words) < 3:

        raise ValueError(
            f"Для дня {day_number + 1} "
            f"недостаточно слов в words.json"
        )

    return today_words


# ============================================================
# ЭТАП УРОКА
# ============================================================

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


# ============================================================
# ПРОСТЫЕ ФРАЗЫ
# ============================================================

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

        "ROADWORK":
            "There is roadwork.",

        "TRAFFIC":
            "There is traffic.",

        "BRAKE":
            "Press the brake.",

        "LEFT":
            "Turn left.",

        "RIGHT":
            "Turn right.",

        "MORNING":
            "Good morning.",

        "NIGHT":
            "Good night.",

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


# ============================================================
# EDGE TTS
# ============================================================

async def make_voice(
    text,
    filename,
    voice,
    rate="-10%"
):

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

        print(
            stderr.decode(
                errors="ignore"
            )
        )

        raise RuntimeError(
            "Ошибка edge-tts"
        )


def run_voice(
    text,
    filename,
    voice
):

    asyncio.run(
        make_voice(
            text,
            filename,
            voice,
            "-10%"
        )
    )


# ============================================================
# СОЗДАНИЕ АУДИО
# ============================================================

def make_audio(words, stage):

    final_file = "lesson.mp3"

    parts = []

    # --------------------------------------------------------
    # УРОК 1
    # --------------------------------------------------------

    if stage == 1:

        for item in words:

            word = item["word"]
            translation = item["translation"]
            association = item["association"]

            # Слово
            parts.append({
                "en": word,
                "ru": ""
            })

            # Ассоциация
            parts.append({
                "en": association,
                "ru": ""
            })

            # Перевод
            parts.append({
                "en": "",
                "ru": translation
            })

            # 10 повторений
            for _ in range(10):

                parts.append({
                    "en": word,
                    "ru": translation
                })

    # --------------------------------------------------------
    # УРОК 2
    # --------------------------------------------------------

    elif stage == 2:

        for item in words:

            word = item["word"]
            translation = item["translation"]

            sentence = make_sentence(word)

            for _ in range(5):

                parts.append({
                    "en": word,
                    "ru": translation
                })

                parts.append({
                    "en": sentence,
                    "ru": translation
                })

    # --------------------------------------------------------
    # УРОК 3 — RECALL
    # --------------------------------------------------------

    elif stage == 3:

        for item in words:

            word = item["word"]
            translation = item["translation"]

            for _ in range(5):

                parts.append({
                    "en": word,
                    "ru": ""
                })

                parts.append({
                    "en": "",
                    "ru": translation
                })

    # --------------------------------------------------------
    # УРОК 4
    # --------------------------------------------------------

    elif stage == 4:

        for item in words:

            word = item["word"]
            translation = item["translation"]

            sentence = make_sentence(word)

            for _ in range(5):

                parts.append({
                    "en": sentence,
                    "ru": translation
                })

                parts.append({
                    "en": word,
                    "ru": translation
                })

    # --------------------------------------------------------
    # УРОК 5
    # --------------------------------------------------------

    else:

        for item in words:

            word = item["word"]
            translation = item["translation"]

            for _ in range(5):

                parts.append({
                    "en": word,
                    "ru": ""
                })

            parts.append({
                "en": "",
                "ru": translation
            })

    # --------------------------------------------------------
    # СОЗДАЁМ КУСКИ АУДИО
    # --------------------------------------------------------

    audio_files = []

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

            audio_files.append(
                en_file
            )

        if ru:

            ru_file = f"ru_{index}.mp3"

            run_voice(
                ru,
                ru_file,
                "ru-RU-DmitryNeural"
            )

            audio_files.append(
                ru_file
            )

    if not audio_files:

        raise RuntimeError(
            "Не создано ни одного аудиофайла"
        )

    # --------------------------------------------------------
    # СПИСОК ДЛЯ FFMPEG
    # --------------------------------------------------------

    list_file = "audio_list.txt"

    with open(
        list_file,
        "w",
        encoding="utf-8"
    ) as f:

        for audio_file in audio_files:

            absolute_path = os.path.abspath(
                audio_file
            )

            f.write(
                f"file '{absolute_path}'\n"
            )

    # --------------------------------------------------------
    # СКЛЕИВАЕМ
    # --------------------------------------------------------

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
        final_file
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

    return final_file


# ============================================================
# ТЕКСТОВОЕ СООБЩЕНИЕ
# ============================================================

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

        body += (
            "\n🎧 Сначала представь картинку."
            "\nПотом слушай."
        )

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
            "Попробуй вспомнить перевод сам."
        )

    elif stage == 4:

        title = "🔄 ТВОРЧЕСКОЕ ПОВТОРЕНИЕ"

        body = (
            "\nСмотрим на знакомые слова "
            "с другой стороны.\n"
            "Слушай фразы и узнавай слова."
        )

    else:

        title = "🎓 ФИНАЛЬНАЯ ПРОВЕРКА"

        body = (
            "\nНе подглядывай.\n"
            "Попробуй самостоятельно "
            "вспомнить все три слова."
        )

    telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text":
                "🇬🇧 ENGLISH RADAR\n\n"
                f"{title}\n"
                f"{body}"
        }
    )


# ============================================================
# ОТПРАВКА АУДИО
# ============================================================

def send_audio(
    filename,
    stage
):

    captions = {

        1:
            "🎧 Новые слова + ассоциации + повторение ×10",

        2:
            "🎧 Повторение №2 — простые фразы",

        3:
            "🎧 RECALL — вспоминаем самостоятельно",

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

    print(
        "TELEGRAM AUDIO RESPONSE:"
    )

    print(
        response.text
    )

    if not response.ok:

        raise RuntimeError(
            "Telegram не принял аудио"
        )


# ============================================================
# ОСНОВНАЯ ПРОГРАММА
# ============================================================

def main():

    now = datetime.now(KYIV)

    print(
        "Kyiv time:",
        now.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    if not TOKEN:

        raise ValueError(
            "TELEGRAM_BOT_TOKEN пустой"
        )

    if not CHAT_ID:

        raise ValueError(
            "TELEGRAM_CHAT_ID пустой"
        )

    print(
        "Chat ID:",
        CHAT_ID[:4] + "***"
    )

    words = get_today_words()

    print(
        "Today's words:",
        [
            item["word"]
            for item in words
        ]
    )

    stage = get_stage()

    print(
        "Stage:",
        stage
    )

    # Сначала проверяем Telegram
    send_text(
        words,
        stage
    )

    # Затем создаём аудио
    filename = make_audio(
        words,
        stage
    )

    # И отправляем
    send_audio(
        filename,
        stage
    )

    print(
        "================================"
    )

    print(
        "ENGLISH RADAR УСПЕШНО ЗАВЕРШИЛ РАБОТУ"
    )

    print(
        "================================"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
