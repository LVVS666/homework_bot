class HTTPStatusError(Exception):
    def __init__(self, text):
        self.txt = text

class NoteAPIOuput(KeyError):
    def __init__(self, text):
        self.txt = text

class UnknownStatus(Exception):
    def __init__(self, text):
        self.txt = text

class NoCorrectFormat(ValueError):
    def __int__(self,text):
        self.txt = text