import os
import json
import time
import subprocess
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# SETTINGS
# ============================================================

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

KYIV = ZoneInfo("Europe/Kyiv")

WORDS_FILE = "words.json"
AUDIO_FILE = "lesson.mp3"

START_DATE = datetime(
    2026, 8, 17,
    tzinfo=KYIV
).date()


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


def send_message(text):

    telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": text
        }
    )


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
            "words.json должен содержать список"
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
            "В words.json недостаточно слов "
            f"для дня {day_number + 1}"
        )

    return today_words


# ============================================================
# STAGE
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
# SENTENCES
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

def make_voice(
    text,
    filename,
    voice
):

    command = [

        "edge-tts",

        "--voice",
        voice,

        "--rate",
        "-15%",

        "--text",
        text,

        "--write-media",
        filename
    ]

    print()
    print("EDGE-TTS:")
    print(text[:150])

    last_error = ""

    for attempt in range(1, 4):

        print(
            f"TTS attempt {attempt}/3"
        )

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:

                if os.path.exists(filename):

                    size = os.path.getsize(
                        filename
                    )

                    if size > 1000:

                        print(
                            "TTS OK:",
                            filename,
                            size,
                            "bytes"
                        )

                        return True

            last_error = (
                result.stderr
                or result.stdout
                or "Unknown edge-tts error"
            )

            print(
                "edge-tts error:"
            )

            print(last_error)

        except Exception as e:

            last_error = str(e)

            print(
                "TTS exception:",
                last_error
            )

        time.sleep(3)

    print()
    print(
        "EDGE-TTS FAILED AFTER 3 ATTEMPTS"
    )

    print(last_error)

    return False


# ============================================================
# AUDIO TEXT
# ============================================================

def build_audio_text(
    item,
    stage
):

    word = item["word"]
    translation = item["translation"]
    sentence = make_sentence(word)

    # --------------------------------------------------------
    # STAGE 1
    # --------------------------------------------------------

    if stage == 1:

        english = (
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}."
        )

        russian = (
            f"{translation}. "
            f"{translation}. "
            f"{translation}."
        )

    # --------------------------------------------------------
    # STAGE 2
    # --------------------------------------------------------

    elif stage == 2:

        english = (
            f"{word}. "
            f"{sentence}. "
            f"{word}. "
            f"{sentence}. "
            f"{word}. "
            f"{sentence}. "
            f"{word}. "
            f"{sentence}. "
            f"{word}. "
            f"{sentence}."
        )

        russian = (
            f"{translation}. "
            f"{translation}. "
            f"{translation}."
        )

    # --------------------------------------------------------
    # STAGE 3
    # --------------------------------------------------------

    elif stage == 3:

        english = (
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}."
        )

        russian = (
            f"{translation}."
        )

    # --------------------------------------------------------
    # STAGE 4
    # --------------------------------------------------------

    elif stage == 4:

        english = (
            f"{sentence}. "
            f"{word}. "
            f"{sentence}. "
            f"{word}. "
            f"{sentence}. "
            f"{word}. "
            f"{sentence}. "
            f"{word}. "
            f"{sentence}. "
            f"{word}."
        )

        russian = (
            f"{translation}. "
            f"{translation}. "
            f"{translation}."
        )

    # --------------------------------------------------------
    # STAGE 5
    # --------------------------------------------------------

    else:

        english = (
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}. "
            f"{word}."
        )

        russian = (
            f"{translation}."
        )

    return english, russian


# ============================================================
# CREATE AUDIO
# ============================================================

def make_audio(
    words,
    stage
):

    print()
    print("==============================")
    print("CREATING AUDIO")
    print("==============================")

    temporary_files = []

    for index, item in enumerate(words):

        print()
        print(
            f"WORD {index + 1}:",
            item["word"]
        )

        english_text, russian_text = (
            build_audio_text(
                item,
                stage
            )
        )

        english_file = (
            f"english_{index}.mp3"
        )

        russian_file = (
            f"russian_{index}.mp3"
        )

        # ----------------------------------------------------
        # ENGLISH
        # ----------------------------------------------------

        ok = make_voice(
            english_text,
            english_file,
            "en-US-GuyNeural"
        )

        if not ok:

            raise RuntimeError(
                "edge-tts не смог создать "
                f"английское аудио для "
                f"{item['word']}"
            )

        temporary_files.append(
            english_file
        )

        # ----------------------------------------------------
        # RUSSIAN
        # ----------------------------------------------------

        ok = make_voice(
            russian_text,
            russian_file,
            "ru-RU-DmitryNeural"
        )

        if not ok:

            raise RuntimeError(
                "edge-tts не смог создать "
                f"русское аудио для "
                f"{item['word']}"
            )

        temporary_files.append(
            russian_file
        )

    # ========================================================
    # FFMPEG LIST
    # ========================================================

    list_file = "audio_list.txt"

    with open(
        list_file,
        "w",
        encoding="utf-8"
    ) as f:

        for filename in temporary_files:

            absolute = os.path.abspath(
                filename
            )

            f.write(
                "file '"
                + absolute.replace(
                    "'",
                    "'\\''"
                )
                + "'\n"
            )

    # ========================================================
    # JOIN
    # ========================================================

    print()
    print("Joining audio with ffmpeg...")

    command = [

        "ffmpeg",

        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        list_file,

        "-c:a",
        "libmp3lame",

        "-b:a",
        "128k",

        AUDIO_FILE
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print(result.stderr)

        raise RuntimeError(
            "Ошибка ffmpeg"
        )

    if not os.path.exists(
        AUDIO_FILE
    ):

        raise RuntimeError(
            "ffmpeg не создал lesson.mp3"
        )

    size = os.path.getsize(
        AUDIO_FILE
    )

    if size < 1000:

        raise RuntimeError(
            "lesson.mp3 получился пустым"
        )

    print()
    print(
        "AUDIO CREATED:",
        size,
        "bytes"
    )

    return AUDIO_FILE


# ============================================================
# TELEGRAM TEXT
# ============================================================

def send_lesson_text(
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
            "Попробуй вспомнить перевод сам.\n"
            "Не подглядывай."
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

    send_message(
        "🇬🇧 ENGLISH RADAR\n\n"
        f"{title}\n"
        f"{body}"
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
            "ассоциации + повторение ×10",

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

    print()
    print("Sending audio to Telegram...")

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

            timeout=180
        )

    print(
        "TELEGRAM AUDIO RESPONSE:"
    )

    print(
        response.text
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):

        raise RuntimeError(
            f"Telegram audio error: {result}"
        )

    print(
        "AUDIO SENT SUCCESSFULLY"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    now = datetime.now(KYIV)

    print()
    print("==============================")
    print("ENGLISH RADAR")
    print("==============================")

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

    # --------------------------------------------------------
    # WORDS
    # --------------------------------------------------------

    words = get_today_words()

    print(
        "Today's words:",
        [
            item["word"]
            for item in words
        ]
    )

    # --------------------------------------------------------
    # STAGE
    # --------------------------------------------------------

    stage = get_stage()

    print(
        "Stage:",
        stage
    )

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    print(
        "Sending lesson text..."
    )

    send_lesson_text(
        words,
        stage
    )

    print(
        "Text sent."
    )

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    filename = make_audio(
        words,
        stage
    )

    # --------------------------------------------------------
    # TELEGRAM AUDIO
    # --------------------------------------------------------

    send_audio(
        filename,
        stage
    )

    # --------------------------------------------------------
    # DONE
    # --------------------------------------------------------

    print()
    print("==============================")
    print(
        "ENGLISH RADAR SUCCESS"
    )
    print("==============================")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()    
