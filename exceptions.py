class HTTP_Status_error(Exception):
    def __init__(self, text):
        self.txt = text