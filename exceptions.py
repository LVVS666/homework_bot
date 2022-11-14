class HTTP_Status_error(Exception):
    def __init__(self, text):
        self.txt = text

class Note_Status_Homework(Exception):
    def __init__(self, text):
        self.txt = 'Отсутствует статус запроса к API '


class KeyNoteHomework(Exception):
    def __init__(self, text):
        self.txt = 'Отсутствует ключ в запросе к API'