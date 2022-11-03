# Homework_bot

## Описание

Телеграмм бот, который работает с API Яндекс.Практикум, проверяет статус сданной домашней работы на ревью.

## Как запустить проект

### Клонировать репозиторий:

git clone git@github.com:Calyps0l/homework_bot.git

### Перейти в него с помощью командной строки:

cd homework_bot

### Создать и активировать виртуальное окружение:

python3 -m venv venv

source venv/bin/activate

### Установить все необходимые зависимости:

pip install -r requirements.txt

### Импортируем токены Яндекс.Практикума и Телеграмма:

export PRACTICUM_TOKEN=<PRACTICUM_TOKEN>

export TELEGRAM_TOKEN=<TELEGRAM_TOKEN>

export CHAT_ID=<CHAT_ID>

### Запускаем проект

python homework.py
