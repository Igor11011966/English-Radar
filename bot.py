import os
import json
import requests
import asyncio
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# ENGLISH RADAR
# ============================================================

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

KYIV = ZoneInfo("Europe/Kyiv")

WORDS_FILE = "words.json"

# Первый учебный день
START_DATE = datetime(
    2026,
    8,
    17,
    tzinfo=KYIV
).date()


# Голоса
ENGLISH_VOICE = "en-US-GuyNeural"
RUSSIAN_VOICE = "ru-RU-DmitryNeural"

# Скорость речи
VOICE_RATE = "-15%"


# ============================================================
# TELEGRAM
# ============================================================

def telegram(method, data=None):

    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    response = requests.post(
        url,
        data=data or {},
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
# WORDS
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

    if len(words) < 3:

        raise ValueError(
            "В words.json должно быть минимум 3 слова"
        )

    return words


def get_today_words():

    words = load_words()

    today = datetime.now(
        KYIV
    ).date()

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
            f"В words.json недостаточно слов "
            f"для дня {day_number + 1}. "
            f"Нужно минимум "
            f"{(day_number + 1) * 3}, "
            f"найдено {len(words)}."
        )

    return today_words


# ============================================================
# STAGE
# ============================================================

def get_stage():

    hour = datetime.now(
        KYIV
    ).hour

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
# SIMPLE SENTENCES
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
        word.upper(),
        word
    )


# ============================================================
# EDGE TTS
# ============================================================

async def make_voice(
    text,
    filename,
    voice,
    rate=VOICE_RATE
):

    command = [

        "edge-tts",

        "--voice",
        voice,

        # ВАЖНО:
        # не разделяем --rate и -15%
        f"--rate={rate}",

        "--text",
        text,

        "--write-media",
        filename
    ]

    print(
        "EDGE TTS:",
        " ".join(command)
    )

    process = await asyncio.create_subprocess_exec(

        *command,

        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:

        error = stderr.decode(
            errors="ignore"
        ).strip()

        print(
            "EDGE-TTS ERROR:",
            error
        )

        raise RuntimeError(
            f"edge-tts не смог создать аудио "
            f"для: {text}\n{error}"
        )

    if (
        not os.path.exists(filename)
        or os.path.getsize(filename) == 0
    ):

        raise RuntimeError(
            f"edge-tts создал пустой файл: "
            f"{filename}"
        )


def run_voice(
    text,
    filename,
    voice
):

    last_error = None

    # До 3 попыток
    for attempt in range(1, 4):

        try:

            asyncio.run(
                make_voice(
                    text,
                    filename,
                    voice
                )
            )

            return

        except Exception as exc:

            last_error = exc

            print(
                f"TTS попытка "
                f"{attempt}/3 неудачна:",
                exc
            )

            if attempt < 3:

                time.sleep(2)

    raise last_error


# ============================================================
# BUILD AUDIO
# ============================================================

def build_parts(
    words,
    stage
):

    parts = []

    # --------------------------------------------------------
    # STAGE 1
    # Новые слова
    # --------------------------------------------------------

    if stage == 1:

        for item in words:

            # Английское слово
            parts.append(
                (
                    "en",
                    item["word"]
                )
            )

            # Перевод
            parts.append(
                (
                    "ru",
                    item["translation"]
                )
            )

            # Ассоциация — русский голос
            parts.append(
                (
                    "ru",
                    item["association"]
                )
            )

            # 10 повторений
            for _ in range(10):

                parts.append(
                    (
                        "en",
                        item["word"]
                    )
                )

                parts.append(
                    (
                        "ru",
                        item["translation"]
                    )
                )

    # --------------------------------------------------------
    # STAGE 2
    # Простые предложения
    # --------------------------------------------------------

    elif stage == 2:

        for item in words:

            sentence = make_sentence(
                item["word"]
            )

            for _ in range(5):

                parts.append(
                    (
                        "en",
                        item["word"]
                    )
                )

                parts.append(
                    (
                        "ru",
                        item["translation"]
                    )
                )

                parts.append(
                    (
                        "en",
                        sentence
                    )
                )

                parts.append(
                    (
                        "ru",
                        item["translation"]
                    )
                )

    # --------------------------------------------------------
    # STAGE 3
    # RECALL
    # --------------------------------------------------------

    elif stage == 3:

        for item in words:

            for _ in range(5):

                parts.append(
                    (
                        "en",
                        item["word"]
                    )
                )

                parts.append(
                    (
                        "ru",
                        item["translation"]
                    )
                )

    # --------------------------------------------------------
    # STAGE 4
    # Творческое повторение
    # --------------------------------------------------------

    elif stage == 4:

        for item in words:

            sentence = make_sentence(
                item["word"]
            )

            for _ in range(5):

                parts.append(
                    (
                        "en",
                        sentence
                    )
                )

                parts.append(
                    (
                        "ru",
                        item["translation"]
                    )
                )

                parts.append(
                    (
                        "en",
                        item["word"]
                    )
                )

                parts.append(
                    (
                        "ru",
                        item["translation"]
                    )
                )

    # --------------------------------------------------------
    # STAGE 5
    # Финальная проверка
    # --------------------------------------------------------

    else:

        for item in words:

            for _ in range(5):

                parts.append(
                    (
                        "en",
                        item["word"]
                    )
                )

            parts.append(
                (
                    "ru",
                    item["translation"]
                )
            )

    return parts


# ============================================================
# CREATE AUDIO
# ============================================================

def make_audio(
    words,
    stage
):

    filename = "lesson.mp3"

    parts = build_parts(
        words,
        stage
    )

    print(
        f"Создаю аудио. "
        f"Stage={stage}, "
        f"частей={len(parts)}"
    )

    files = []

    try:

        for index, (
            language,
            text
        ) in enumerate(parts):

            if not text:
                continue

            if language == "en":

                audio_file = (
                    f"audio_{index:03d}_en.mp3"
                )

                voice = ENGLISH_VOICE

            else:

                audio_file = (
                    f"audio_{index:03d}_ru.mp3"
                )

                voice = RUSSIAN_VOICE

            run_voice(
                text,
                audio_file,
                voice
            )

            files.append(
                audio_file
            )

        if not files:

            raise RuntimeError(
                "Не создано ни одного аудиофайла"
            )

        # ----------------------------------------------------
        # FFmpeg
        # ----------------------------------------------------

        list_file = "audio_list.txt"

        with open(
            list_file,
            "w",
            encoding="utf-8"
        ) as f:

            for audio_file in files:

                absolute = os.path.abspath(
                    audio_file
                )

                safe_path = (
                    absolute
                    .replace(
                        "'",
                        "'\\''"
                    )
                )

                f.write(
                    f"file '{safe_path}'\n"
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

            print(
                result.stderr
            )

            raise RuntimeError(
                "Ошибка объединения аудио "
                "через ffmpeg"
            )

        if (
            not os.path.exists(filename)
            or os.path.getsize(filename) == 0
        ):

            raise RuntimeError(
                "ffmpeg не создал lesson.mp3"
            )

        print(
            "Аудио готово:",
            filename,
            os.path.getsize(filename),
            "bytes"
        )

        return filename

    finally:

        # Удаляем временные кусочки

        for audio_file in files:

            try:

                os.remove(
                    audio_file
                )

            except OSError:
                pass

        try:

            os.remove(
                "audio_list.txt"
            )

        except OSError:
            pass


# ============================================================
# SEND TEXT
# ============================================================

def send_text(
    words,
    stage
):

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
            "\n🎧 Сначала представь картинку. "
            "Потом слушай."
        )

    elif stage == 2:

        title = "🔄 ПОВТОРЕНИЕ №2"

        body = ""

        for item in words:

            body += (

                f"\n{item['word']}\n"

                f"👉 "
                f"{make_sentence(item['word'])}\n"

                f"🇷🇺 "
                f"{item['translation']}\n"
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
# SEND AUDIO
# ============================================================

def send_audio(
    filename,
    stage
):

    captions = {

        1:
            "🎧 Новые слова + "
            "ассоциации + 10 повторений",

        2:
            "🎧 Повторение №2 — "
            "простые фразы",

        3:
            "🎧 RECALL — "
            "вспоминаем самостоятельно",

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

                "chat_id":
                    CHAT_ID,

                "caption":
                    captions.get(
                        stage,
                        "🎧 English Radar"
                    )
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
        "Telegram audio:",
        response.text
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):

        raise RuntimeError(
            f"Telegram не принял аудио: "
            f"{result}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    now = datetime.now(
        KYIV
    )

    print("=" * 32)
    print("ENGLISH RADAR")
    print("=" * 32)

    print(
        "Kyiv time:",
        now.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    print(
        "Chat ID:",
        CHAT_ID[:4] + "***"
    )

    # Получаем три слова сегодняшнего дня

    words = get_today_words()

    print(
        "Today's words:",
        [
            item["word"]
            for item in words
        ]
    )

    # Определяем этап

    stage = get_stage()

    print(
        "Stage:",
        stage
    )

    # Сначала текст

    send_text(
        words,
        stage
    )

    # Затем аудио

    filename = make_audio(
        words,
        stage
    )

    # Отправляем аудио

    send_audio(
        filename,
        stage
    )

    print(
        "English Radar "
        "успешно завершил урок."
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
