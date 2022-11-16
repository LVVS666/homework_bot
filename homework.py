import logging
import os
import sys
import time
from http import HTTPStatus

import telegram.error
import requests
from dotenv import load_dotenv
import telegram

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

TELEGRAM_RETRY_TIME = 600
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
    except telegram.error.TelegramError as error:
        logging.error(f'Ошибка к обращению API  telegram {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_response = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=params
                                         )
        homework_statuses = homework_response.json()
    except requests.exceptions.RequestException as original_error:
        raise exceptions.NoCorrectFormat(''
                                         'В ответ пришел '
                                         'некоретный формат'
                                         ) \
            from original_error
    if homework_response.status_code != HTTPStatus.OK:
        raise exceptions.HTTPStatusError('Ошибка в обращении к API')
    return homework_statuses


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not response['current_date']:
        raise KeyError(
            'Ключ current_date в ответе API Яндекс.Практикум отсутствует'
        )
    if not response['homeworks']:
        raise KeyError(
            'Ключ homeworks в ответе API Яндекс.Практикум отсутствует'
        )
    timestamp = response['current_date']
    homeworks = response['homeworks']
    if not isinstance(timestamp, int) and isinstance(homeworks, list) is None:
        raise exceptions.NoteAPIOuput('Формат ответа от API '
                                      'несоответствует формату JSON.'
                                      )
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ “homework_name” отсутствует в словаре homework')
    if 'status' not in homework:
        raise KeyError('Ключ "status" отсутствует в словаре homework')
    homework_name = homework['homework_name']
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise exceptions.UnknownStatus(
            f'Неизвестный статус {homework_status} работы {homework_name}'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = {
        'practicum_token': PRACTICUM_TOKEN,
        'telegram_token': TELEGRAM_TOKEN,
        'telegram_chat_token': TELEGRAM_CHAT_ID
    }

    for _, value in tokens.items():
        list_tokken_missing = []
        if value is None:
            list_tokken_missing.append(value)
        else:
            return True
        logging.error(f'{list_tokken_missing} токены отсутствуют')
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)
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
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            send_message(bot, message)
        finally:
            time.sleep(TELEGRAM_RETRY_TIME)


if __name__ == '__main__':
    main()
