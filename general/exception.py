"""
自定义异常，见名知意
"""


class InvalidArgumentException(Exception):
    pass


class UserAlreadyExistException(Exception):
    pass


class UserDoesNotExistException(Exception):
    pass


class TokenTimeOutException(Exception):
    pass


class IllegalTokenException(Exception):
    pass
