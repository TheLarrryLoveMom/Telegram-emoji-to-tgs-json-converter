# Emoji Export Bot

Telegram-бот, который по ссылке `https://t.me/addemoji/<pack_name>` скачивает все кастом-эмодзи `.tgs`, валидирует их, собирает `manifest.json` и отправляет ZIP-архив пользователю.

## Возможности

- Валидация `.tgs` (gzip + Lottie JSON)
- Лимиты на количество эмодзи и размер архива
- Прогресс-сообщения пользователю
- Выбор формата экспорта: `tgs` или `json`
- Управление через inline-кнопки в одном меню
- Экспорт по ссылке на пак или по списку эмодзи из одного сообщения

## Требования

- Python 3.11+
- Node.js + PM2 (`npm i -g pm2`)

## Установка

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Создайте `.env` на основе `.env.example` и укажите токен бота:

```env
BOT_TOKEN=123456:ABCDEF
```

## Запуск через PM2

```bash
pm2 start ecosystem.config.js
pm2 logs emoji-export-bot
pm2 restart emoji-export-bot
pm2 stop emoji-export-bot
pm2 save
pm2 startup
```

## Быстрый запуск через Windows Terminal

```bash
cd C:\Users\Larrygraphic\Desktop\TgsToJsonBot
.\.venv\Scripts\activate
python -m bot.main
```

Если окружения ещё нет:

```bash
cd C:\Users\Larrygraphic\Desktop\TgsToJsonBot
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m bot.main
```

## Как использовать

1. Нажмите `/start`
2. Выберите формат кнопкой `Экспорт TGS` или `Экспорт JSON`
3. Отправьте ссылку на пак или просто несколько кастом-эмодзи в одном сообщении:

```
https://t.me/addemoji/woxystudioo
```

Бот ответит прогрессом и вернёт ZIP:

```
export_<pack_name>_<timestamp>.zip
  manifest.json
  assets/
    0000.tgs или 0000.json
    0001.tgs или 0001.json
    ...
```

## Примечания

- Источник всегда `.tgs`, но можно экспортировать в `.tgs` или в распакованный `.json`.
- Если файл не проходит валидацию, экспорт прерывается с понятной причиной.