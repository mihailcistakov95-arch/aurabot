# Aura Telegram-бот

Бот рассказывает про приложение Aura и отдаёт APK файлом прямо в чат.
`/start` — описание и кнопки, «⬇️ Скачать APK» — присылает файл.

## 1. Создать бота в Telegram

1. Открой Telegram, напиши **@BotFather**.
2. Команда `/newbot`, придумай имя и username (должен заканчиваться на `bot`).
3. BotFather пришлёт токен вида `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` — сохрани его, он понадобится ниже.

## 2. Залить код на GitHub

Render разворачивает из git-репозитория, поэтому папку `telegram-bot` нужно запушить в GitHub:

```bash
cd telegram-bot
git init
git add .
git commit -m "Aura telegram bot"
git branch -M main
git remote add origin https://github.com/<твой-аккаунт>/aura-bot.git
git push -u origin main
```

(репозиторий на GitHub нужно сначала создать пустым на github.com — New repository)

## 3. Развернуть на Render (бесплатно, без карты)

1. Зарегистрируйся на [render.com](https://render.com) (можно через GitHub-аккаунт).
2. **New → Web Service**, выбери репозиторий `aura-bot`.
3. Настройки:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn bot:app`
   - **Instance Type**: Free
4. В разделе **Environment** добавь переменные:
   - `BOT_TOKEN` — токен от BotFather
   - `WEBHOOK_SECRET` — любая длинная случайная строка (например, сгенерируй на [random.org](https://www.random.org/strings/))
5. Нажми **Create Web Service** и дождись деплоя. Render выдаст публичный адрес вида `https://aura-bot-xxxx.onrender.com`.

## 4. Зарегистрировать вебхук

Один раз после деплоя (и после каждого изменения адреса) сообщи Telegram, куда слать сообщения.
Выполни у себя локально (нужен Python и `pip install requests`):

```bash
BOT_TOKEN=токен_от_BotFather WEBHOOK_SECRET=та_же_строка_что_в_Render PUBLIC_URL=https://aura-bot-xxxx.onrender.com python set_webhook.py
```

В Windows PowerShell переменные окружения задаются так:

```powershell
$env:BOT_TOKEN="токен"; $env:WEBHOOK_SECRET="строка"; $env:PUBLIC_URL="https://aura-bot-xxxx.onrender.com"; python set_webhook.py
```

Должен вывестись ответ `200 {'ok': True, 'result': True, ...}`.

## 5. Проверить

Напиши своему боту в Telegram `/start` — должно прийти описание с кнопками.

## Про бесплатный тариф Render

Бесплатный Web Service «засыпает» после ~15 минут без запросов. Первое сообщение
после простоя придёт с задержкой в 30-60 секунд, пока сервер просыпается —
дальше отвечает мгновенно. Если это критично, можно раз в 10 минут пинговать
`https://aura-bot-xxxx.onrender.com/` бесплатным сервисом [UptimeRobot](https://uptimerobot.com/),
тогда бот почти не будет засыпать.

## Обновить APK в боте

Когда выйдет новая версия приложения — замени файл `assets/aura.apk` на свежий,
закоммить и запушь (`git add`, `git commit`, `git push`) — Render передеплоит
сервис автоматически.

## Локальная проверка без деплоя (необязательно)

Если на компьютере есть Python:

```bash
pip install -r requirements.txt
BOT_TOKEN=токен python bot.py --poll
```

Это запустит бота в режиме поллинга (без вебхука) — удобно, чтобы быстро
проверить логику, прежде чем деплоить. Для постоянной работы всё равно
нужен вебхук на Render — поллинг работает только пока запущен скрипт.
