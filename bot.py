import os
import asyncio
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()


def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=30
    )

    print("MESSAGE:", response.text)

    response.raise_for_status()


async def make_voice(text, filename):

    command = [
        "edge-tts",
        "--voice",
        "en-US-GuyNeural",
        "--rate",
        "-15%",
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

        print(
            stderr.decode(
                errors="ignore"
            )
        )

        raise RuntimeError(
            "edge-tts failed"
        )


def make_audio():

    filename = "english_radar_test.mp3"

    text = (
        "Road. Road. Road. "
        "Road means doroga. "
        "The road is long."
    )

    asyncio.run(
        make_voice(
            text,
            filename
        )
    )

    return filename


def send_audio(filename):

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
                "caption": "English Radar - test lesson"
            },

            files={
                "audio": (
                    filename,
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

    if not TOKEN:

        raise ValueError(
            "TELEGRAM_BOT_TOKEN empty"
        )

    if not CHAT_ID:

        raise ValueError(
            "TELEGRAM_CHAT_ID empty"
        )

    print(
        "English Radar: start"
    )

    send_message(
        "ENGLISH RADAR\n\n"
        "Telegram connected.\n"
        "Now testing audio."
    )

    filename = make_audio()

    send_audio(
        filename
    )

    print(
        "English Radar: SUCCESS"
    )


if __name__ == "__main__":

    main()
