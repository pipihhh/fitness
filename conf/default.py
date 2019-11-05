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


class DefaultConfig(BaseConfig):
    pass
