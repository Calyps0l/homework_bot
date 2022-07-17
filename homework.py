import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

logging.basicConfig(
    level=logging.DEBUG,
    filemode='w',
    filename='prog.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения о статусе работы."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправлено')
    except telegram.TelegramError as telegram_error:
        logger.error(f'Ошибка при отправке сообщения: {telegram_error}')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        logger.info('Попытка коннекта к эндпоинту')
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            api_message = (
                f'Эндпоинт недоступен'
                f'Код ответа API: {response.status_code}')
            raise exceptions.StatusCodeError(api_message)
    except Exception as error:
        raise Exception(f'Ошибка запроса к API: {error}')
    else:
        return response.json()


def check_response(response):
    """Проверка API ответа."""
    if response is None:
        response_message = (
            'Неккоректный API ответ при обращении'
            'к ключу homeworks')
        raise exceptions.ResponseError(response_message)
    if not isinstance(response, dict):
        response_message = ('Неккоректные значения в API ответе')
        raise TypeError(response_message)
    if 'homeworks' not in response:
        response_message = ('Ошибка доступа к ключу homeworks')
        raise KeyError(response_message)
    if not response['homeworks']:
        return {}
    hw_list = response.get('homeworks')
    if not isinstance(hw_list, list):
        response_message = ('Список с ключом homeworks отсутсует')
        raise TypeError(response_message)
    return hw_list


def parse_status(homework):
    """Получаем информацию об изменениях статуса работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        status_message = 'Ошибка доступа к homework_name'
        raise KeyError(status_message)
    if homework_status is None:
        status_message = 'Ошибка доступа к homework_status'
        raise KeyError(status_message)
    if homework_status not in HOMEWORK_STATUSES:
        status_message = 'Неизвестный статус проверки работы'
        raise ValueError(status_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    tokens_status = True
    tokens_message = ('Обязательный токен отсутствует:')
    if PRACTICUM_TOKEN is None:
        tokens_status = False
        logger.critical(
            f'{tokens_message} PRACTICUM_TOKEN')
    if TELEGRAM_TOKEN is None:
        tokens_status = False
        logger.critical(
            f'{tokens_message} TELEGRAM_TOKEN'
        )
    if TELEGRAM_CHAT_ID is None:
        tokens_status = False
        logger.critical(
            f'{tokens_message} TELEGRAM_CHAT_ID'
        )
    return tokens_status


def main():
    """Основная логика работы бота."""
    token_message = 'Ошибка в проверке токенов'
    if not check_tokens():
        raise exceptions.TokenError(token_message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_status = ''
    errors = True
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework and old_status != homework['status']:
                message = parse_status(homework)
                send_message(bot, message)
                old_status = homework['status']
            logger.info('Изменения отсутсвуют, ожидаем 10 минут')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if errors:
                errors = False
                send_message(bot, message)
            logger.critical(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
