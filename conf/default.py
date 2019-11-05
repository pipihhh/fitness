class BaseConfig(object):
    DB_NAME = "ezgym"
    DB_USER = "root"
    DB_PASSWORD = "root"
    DB_PORT = 3306
    DB_HOST = "localhost"
    DB_CHARSET = "utf8"
    DEBUG = True
    SALT = "jsjkfhaskjhdjkashkfj"


class DefaultConfig(BaseConfig):
    pass
