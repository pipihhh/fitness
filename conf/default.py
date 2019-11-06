import os


class BaseConfig(object):
    """
    默认的配置类，包括数据库连接池的配置和密码加盐的配置
    还有是否是调试环境
    """
    DB_NAME = "ezgym"
    DB_USER = "root"
    DB_PASSWORD = "root"
    DB_PORT = 3306
    DB_HOST = "localhost"
    DB_CHARSET = "utf8"
    DEBUG = True
    SALT = "jsjkfhaskjhdjkashkfj"
    JWT_TYPE = "JWT"
    JWT_ALG = "sha256"
    EXP_MIN = 5
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class DefaultConfig(BaseConfig):
    MEDIA_DIR = os.path.join(os.getcwd(), "media", "images")
    MEDIA_URL = "/media/images"
