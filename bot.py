import os
import asyncio
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()


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


async def make_voice(text, filename):
    command = [
        "edge-tts",
        "--voice",
        "en-US-GuyNeural",
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
        print(stderr.decode(errors="ignore"))
        raise RuntimeError("edge-tts не смог создать аудио")


def make_audio():
    filename = "english_radar_test.mp3"

    text = (
        "Road. "
        "Road. "
        "Road. "
        "Road means дорога. "
        "The road is long. "
        "Road."
    )

    asyncio.run(
        make_voice(text, filename)
    )

    if not os.path.exists(filename):
        raise RuntimeError("Аудиофайл не создан")

    if os.path.getsize(filename) == 0:
        raise RuntimeError("Аудиофайл пустой")

    print(
        "Audio created:",
        filename,
        os.path.getsize(filename),
        "bytes"
    )

    return filename


def send_audio(filename):
    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"

    with open(filename, "rb") as audio:

        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": "🎧 English Radar — тест аудио"
            },
            files={
                "audio": (
                    "english_radar_test.mp3",
                    audio,
                    "audio/mpeg"
                )
            },
            timeout=120
        )

    print("AUDIO:", response.text)

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(result)


def main():

    print("=== ENGLISH RADAR AUDIO TEST ===")

    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN пустой")

    if not CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID пустой")

    # Сначала проверяем текст.
    telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": "🎧 English Radar: начинаю тест аудио."
        }
    )

    # Создаём голос.
    filename = make_audio()

    # Отправляем голос.
    send_audio(filename)

    # Финальное сообщение.
    telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": "✅ Тест аудио завершён."
        }
    )

    print("=== SUCCESS ===")


if __name__ == "__main__":
    main()
