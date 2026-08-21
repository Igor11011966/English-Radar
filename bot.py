import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


def telegram(method, data=None):
    response = requests.post(
        f"{BASE_URL}/{method}",
        data=data or {},
        timeout=30
    )

    print(f"\n{method}:")
    print(response.text)

    return response.json()


def main():

    print("=== TELEGRAM TEST ===")
    print("CHAT_ID exists:", bool(CHAT_ID))
    print("CHAT_ID length:", len(CHAT_ID))

    # 1. Проверяем самого бота
    me = telegram("getMe")

    if not me.get("ok"):
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN НЕ РАБОТАЕТ"
        )

    print(
        "BOT:",
        me["result"]["username"]
    )

    # 2. Проверяем Chat ID
    chat = telegram(
        "getChat",
        {
            "chat_id": CHAT_ID
        }
    )

    if not chat.get("ok"):

        print(
            "\n❌ CHAT_ID НЕ НАЙДЕН"
        )

        raise RuntimeError(
            "Telegram не может найти указанный CHAT_ID"
        )

    print(
        "\n✅ CHAT_ID НАЙДЕН"
    )

    print(
        "CHAT TYPE:",
        chat["result"].get("type")
    )

    print(
        "CHAT TITLE:",
        chat["result"].get("title")
    )

    print(
        "CHAT USERNAME:",
        chat["result"].get("username")
    )

    # 3. Пробуем отправить сообщение
    message = telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": "✅ ENGLISH RADAR: Telegram работает!"
        }
    )

    if not message.get("ok"):

        raise RuntimeError(
            "CHAT найден, но Telegram запрещает отправку"
        )

    print(
        "\n🎉 TELEGRAM ПОЛНОСТЬЮ РАБОТАЕТ"
    )


if __name__ == "__main__":
    main()
