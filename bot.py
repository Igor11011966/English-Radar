import os
import json
import asyncio
import subprocess
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import edge_tts

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

KYIV = ZoneInfo("Europe/Kyiv")
WORDS_FILE = "words.json"
START_DATE = datetime(2026, 8, 17, tzinfo=KYIV).date()


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    r = requests.post(url, data=data or {}, timeout=30)
    print("Telegram:", r.text)
    r.raise_for_status()
    result = r.json()
    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Telegram error"))
    return result


def load_words():
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("words.json должен содержать список")
    return data


def get_today_words():
    words = load_words()
    today = datetime.now(KYIV).date()
    day = max(0, (today - START_DATE).days)
    selected = words[day * 3: day * 3 + 3]
    if len(selected) < 3:
        raise ValueError("В words.json недостаточно слов для сегодняшнего дня")
    return selected


def get_stage():
    h = datetime.now(KYIV).hour
    if h < 9:
        return 1
    if h < 11:
        return 2
    if h < 13:
        return 3
    if h < 15:
        return 4
    return 5


def sentence(word):
    return {
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
    }.get(word, word)


async def create_voice(text, filename, voice):
    communicate = edge_tts.Communicate(text, voice, rate="-15%")
    await communicate.save(filename)


def make_parts(words, stage):
    parts = []

    def add(en="", ru=""):
        if en:
            parts.append((en, "en-US-GuyNeural"))
        if ru:
            parts.append((ru, "ru-RU-DmitryNeural"))

    for item in words:
        w = item["word"]
        ru = item["translation"]

        if stage == 1:
            add(w, ru)
            add(item["association"], ru)
            for _ in range(10):
                add(w, ru)

        elif stage == 2:
            s = sentence(w)
            for _ in range(5):
                add(w, ru)
                add(s, ru)

        elif stage == 3:
            for _ in range(5):
                add(w)
                add("", ru)

        elif stage == 4:
            s = sentence(w)
            for _ in range(5):
                add(s, ru)
                add(w, ru)

        else:
            for _ in range(5):
                add(w)
            add("", ru)

    return parts


def make_audio(words, stage):
    files = []
    parts = make_parts(words, stage)

    for i, (text, voice) in enumerate(parts):
        filename = f"part_{i}.mp3"
        print(f"Audio {i + 1}/{len(parts)}: {text}")

        try:
            asyncio.run(create_voice(text, filename, voice))
        except Exception as e:
            print("EDGE-TTS ERROR:", repr(e))
            raise RuntimeError(f"Не удалось создать аудио: {e}") from e

        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            raise RuntimeError(f"edge-tts создал пустой файл: {filename}")

        files.append(filename)

    with open("audio_list.txt", "w", encoding="utf-8") as f:
        for name in files:
            f.write(f"file '{os.path.abspath(name)}'\n")

    result = subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", "audio_list.txt", "-c", "copy", "lesson.mp3"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("ffmpeg не смог собрать lesson.mp3")

    return "lesson.mp3"


def send_text(words, stage):
    titles = {
        1: "🌅 НОВЫЕ СЛОВА",
        2: "🔄 ПОВТОРЕНИЕ №2",
        3: "🧠 RECALL",
        4: "🔄 ТВОРЧЕСКОЕ ПОВТОРЕНИЕ",
        5: "🎓 ФИНАЛЬНАЯ ПРОВЕРКА"
    }

    if stage == 1:
        body = "".join(
            f"\n🔊 {x['word']}\n🇷🇺 {x['translation']}\n🧠 {x['association']}\n"
            for x in words
        )
    elif stage == 2:
        body = "".join(
            f"\n{x['word']}\n👉 {sentence(x['word'])}\n🇷🇺 {x['translation']}\n"
            for x in words
        )
    elif stage == 3:
        body = "\nСначала услышь слово и вспомни перевод сам."
    elif stage == 4:
        body = "\nСлушай фразы и узнавай знакомые слова."
    else:
        body = "\nПопробуй самостоятельно вспомнить все три слова."

    telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": f"🇬🇧 ENGLISH RADAR\n\n{titles[stage]}\n{body}"
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

    with open(filename, "rb") as audio:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendAudio",
            data={
                "chat_id": CHAT_ID,
                "caption": captions[stage]
            },
            files={
                "audio": ("lesson.mp3", audio, "audio/mpeg")
            },
            timeout=120
        )

    print("Telegram audio:", r.text)
    r.raise_for_status()

    if not r.json().get("ok"):
        raise RuntimeError(
            r.json().get("description", "Telegram audio error")
        )


def main():
    print("Kyiv time:", datetime.now(KYIV).strftime("%Y-%m-%d %H:%M"))
    print("CHAT_ID:", CHAT_ID[:4] + "***")

    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN пустой")

    if not CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID пустой")

    words = get_today_words()
    stage = get_stage()

    print("Today's words:", [x["word"] for x in words])
    print("Stage:", stage)

    send_text(words, stage)

    print("Начинаю создание аудио...")
    filename = make_audio(words, stage)

    print("Аудио создано. Отправляю...")
    send_audio(filename, stage)

    print("ENGLISH RADAR: УСПЕШНО")


if __name__ == "__main__":
    main()
