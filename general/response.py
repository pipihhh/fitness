class Response(object):
    def __init__(self):
        self.errno = 0
        self.code = 200
        self.data = None

    @property
    def dict_data(self):
        return self.__dict__
