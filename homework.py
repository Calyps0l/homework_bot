import logging
import os
import sys
import time
from http import HTTPStatus
from json.decoder import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv

import exceptions

logging.basicConfig(
    level=logging.DEBUG,
    filemode='w',
    filename='prog.log',
    format='%(asctime)s, %(levelname)s, %(funcName)s,  %(message)s, %(name)s'
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
    data = {'url': ENDPOINT, 'headers': HEADERS, 'params': params}
    try:
        logger.info('Попытка коннекта к эндпоинту')
        response = requests.get(**data)
        if response.status_code != HTTPStatus.OK:
            api_message = (
                f'Ошибка при ответе сервера'
                f'Код ответа API: {response.status_code}'
                f'Параметры: {data}')
            raise exceptions.StatusCodeError(api_message)
    except requests.RequestException as error:
        api_message = (
            f'Эндпоинт недоступен'
            f'Код ответа API: {error}'
            f'Параметры: {data}')
        raise requests.RequestException(api_message)
    try:
        return response.json()
    except JSONDecodeError as error:
        logger.error(f'Ошибка преобразования ответа в json: {error}')
        raise JSONDecodeError


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
    hw_list = response.get('homeworks')
    if hw_list is None:
        response_message = ('Ошибка доступа к ключу homeworks')
        raise KeyError(response_message)
    if not isinstance(hw_list, list):
        response_message = ('Список с ключом homeworks отсутстует')
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
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Переменные окружения отсутствуют')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            current_timestamp = response.get('current_date')
            if homework:
                message = parse_status(homework[0])
                send_message(bot, message)
            else:
                logger.debug('Новый статус работы отсутствует')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != old_message:
                old_message = message
                send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
