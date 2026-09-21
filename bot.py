"""
Телеграм-бот Aura: рассказывает о приложении и отдаёт APK для скачивания.

Продакшен (Render и т.п.): работает как Flask-приложение, принимает апдейты
через вебхук на /webhook/<WEBHOOK_SECRET>. Запуск: gunicorn bot:app

Локальная проверка без публичного URL: python bot.py --poll
(поллинг — только для разработки, для постоянной работы используется вебхук)
"""

import json
import logging
import os
import sys

import requests
from flask import Flask, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("aura-bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "changeme")
AUTHOR_CHAT_ID = os.environ.get("AUTHOR_CHAT_ID", "")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
APK_PATH = os.path.join(ASSETS_DIR, "aura.apk")
BANNER_PATH = os.path.join(ASSETS_DIR, "banner.png")

APP_DESCRIPTION = (
    "🌿 *Aura* — приложение, которое помогает меньше залипать в телефоне.\n\n"
    "• Пауза перед входом в отвлекающие приложения\n"
    "• Дневные лимиты на приложения и отдельно на музыку\n"
    "• Режим фокуса и режим дисциплины (снимается непросто)\n"
    "• Блокировка сайтов, ключевых слов и YouTube Shorts\n"
    "• Статистика использования и сравнение с друзьями\n\n"
    "Приложение для Android, распространяется напрямую (не из Google Play)."
)

INSTALL_NOTE = (
    "Это APK не из Google Play, поэтому Android при установке может показать "
    "предупреждение — это нормально для файлов вне официального магазина. "
    "Открой файл и разреши установку из этого источника, если система спросит.\n\n"
    "Чтобы приложение заработало полностью, ему нужно выдать несколько "
    "разрешений — это можно сделать прямо во вкладке «Разрешения» внутри Aura "
    "после установки."
)

UNKNOWN_TEXT = "Не понял команду. Нажми /start, чтобы увидеть меню."

DONATE_URL = "https://dalink.to/empyre9n"

FEEDBACK_PROMPT = "✍️ Напиши сюда любое сообщение — отзыв, идею или баг — и я передам его автору."
FEEDBACK_SENT = "Спасибо! Передал автору 🙌"
FEEDBACK_UNAVAILABLE = "Приём отзывов сейчас не настроен, попробуй позже."

MAIN_MENU = {
    "inline_keyboard": [
        [{"text": "⬇️ Скачать APK", "callback_data": "download"}],
        [{"text": "💬 Отзывы и предложения", "callback_data": "feedback"}],
        [{"text": "💚 Поддержать автора", "url": DONATE_URL}],
    ]
}


def api_post(method: str, **kwargs):
    try:
        resp = requests.post(f"{API_URL}/{method}", timeout=kwargs.pop("timeout", 15), **kwargs)
        if not resp.ok:
            log.warning("Telegram API %s failed: %s", method, resp.text)
        return resp
    except requests.RequestException:
        log.exception("Telegram API %s raised", method)
        return None


def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    api_post("sendMessage", json=payload)


def send_welcome(chat_id):
    if not os.path.exists(BANNER_PATH):
        send_message(chat_id, APP_DESCRIPTION, reply_markup=MAIN_MENU)
        log.error("Banner not found at %s", BANNER_PATH)
        return
    with open(BANNER_PATH, "rb") as f:
        api_post(
            "sendPhoto",
            data={
                "chat_id": chat_id,
                "caption": APP_DESCRIPTION,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(MAIN_MENU),
            },
            files={"photo": ("aura-banner.png", f, "image/png")},
            timeout=30,
        )


def forward_feedback(msg: dict):
    chat_id = msg["chat"]["id"]
    text = (msg.get("text") or "").strip()

    # Чтобы найти свой AUTHOR_CHAT_ID в логах Render: он всегда печатается сюда
    log.info("Message from chat_id=%s: %s", chat_id, text[:200])

    if not AUTHOR_CHAT_ID:
        send_message(chat_id, FEEDBACK_UNAVAILABLE)
        return

    if str(chat_id) == str(AUTHOR_CHAT_ID):
        # Автор пишет сам себе (например, тестирует бота) — пересылать некуда
        send_message(chat_id, "Это твой собственный чат с ботом — некому пересылать 🙂")
        return

    sender = msg.get("from", {})
    username = sender.get("username")
    name = sender.get("first_name", "")
    who = f"@{username}" if username else name or "аноним"
    forwarded = f"💬 Отзыв от {who} (id {chat_id}):\n\n{text}"
    send_message(AUTHOR_CHAT_ID, forwarded, parse_mode=None)
    send_message(chat_id, FEEDBACK_SENT)


def send_apk(chat_id):
    if not os.path.exists(APK_PATH):
        send_message(chat_id, "Файл APK сейчас недоступен на сервере, напиши автору бота.")
        log.error("APK not found at %s", APK_PATH)
        return
    with open(APK_PATH, "rb") as f:
        api_post(
            "sendDocument",
            data={"chat_id": chat_id, "caption": INSTALL_NOTE},
            files={"document": ("Aura.apk", f, "application/vnd.android.package-archive")},
            timeout=120,
        )


def handle_update(update: dict):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()
        if text.startswith("/start") or text.startswith("/help"):
            send_welcome(chat_id)
        elif text.startswith("/download"):
            send_apk(chat_id)
        elif text.startswith("/"):
            send_message(chat_id, UNKNOWN_TEXT)
        else:
            # Любое обычное сообщение (не команда) считаем отзывом/предложением
            forward_feedback(msg)
        return

    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq.get("data")
        api_post("answerCallbackQuery", json={"callback_query_id": cq["id"]})
        if data == "download":
            send_apk(chat_id)
        elif data == "feedback":
            send_message(chat_id, FEEDBACK_PROMPT)
        return


app = Flask(__name__)


@app.get("/")
def health():
    return "Aura bot is running", 200


@app.post(f"/webhook/{WEBHOOK_SECRET}")
def webhook():
    handle_update(request.get_json(force=True, silent=True) or {})
    return "ok", 200


def run_polling():
    log.info("Starting in local polling mode (dev only, do not use in production)")
    offset = None
    while True:
        params = {"timeout": 30}
        if offset is not None:
            params["offset"] = offset
        resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=40).json()
        for upd in resp.get("result", []):
            offset = upd["update_id"] + 1
            handle_update(upd)


if __name__ == "__main__":
    if not BOT_TOKEN:
        sys.exit("Set the BOT_TOKEN environment variable first.")
    if "--poll" in sys.argv:
        run_polling()
    else:
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
