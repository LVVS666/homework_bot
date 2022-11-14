import logging
import os
import time
import telegram

from http import HTTPStatus

import requests
from dotenv import load_dotenv


import exceptions


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename=os.path.join(os.path.dirname(__file__), 'main.log'),
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


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
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        print(f'Ошибка к обращению API  telegram {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    homework_statuses = homework_response.json()

    if homework_response.status_code == HTTPStatus.OK:
        return homework_statuses
    else:
        raise exceptions.HTTP_Status_error('Ошибка в обращении к API')


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        timestamp = response['current_date']
    except KeyError:
        logging.error(
            'Ключ current_date в ответе API Яндекс.Практикум отсутствует'
        )
    try:
        homeworks = response['homeworks']
    except KeyError:
        logging.error(
            'Ключ homeworks в ответе API Яндекс.Практикум отсутствует'
        )
    if isinstance(timestamp, int) and isinstance(homeworks, list):
        return homeworks
    else:
        raise Exception


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework['name']
    homework_status = homework.get('status')
    if homework_status is None:
        raise exceptions.HTTP_Status_error(
            'Отстутвует ключ статуса проверки домашней работы'
        )
    if homework_status is HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES.get('homework_status')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        raise Exception('Отсутствует статус домашней работы')


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if all([PRACTICUM_TOKEN,
           TELEGRAM_TOKEN,
           TELEGRAM_CHAT_ID]) is None:
        logging.error('TOKEN NOT_FOUND')
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())
        while True:
            try:
                response = get_api_answer(current_timestamp)
                homework = check_response(response)
                count_homework = len(homework)
                if count_homework > 0:
                    message = parse_status(homework[count_homework - 1])
                    send_message(bot, message)
                    count_homework -= 1
                    current_timestamp = int(time.time())
                    time.sleep(RETRY_TIME)
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
