"""
Регистрирует вебхук в Telegram после того, как бот уже задеплоен и имеет публичный URL.
Запуск (один раз после каждого деплоя на новый адрес):

    BOT_TOKEN=... WEBHOOK_SECRET=... PUBLIC_URL=https://your-app.onrender.com python set_webhook.py
"""

import os
import sys

import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")

if not (BOT_TOKEN and WEBHOOK_SECRET and PUBLIC_URL):
    sys.exit("Нужны переменные окружения BOT_TOKEN, WEBHOOK_SECRET и PUBLIC_URL.")

url = f"{PUBLIC_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET}"
resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", json={"url": url})
print(resp.status_code, resp.json())
