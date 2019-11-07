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
    EXP_MIN = 30
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    PAGE_OFFSET = 3   # 分页相关，每页显示的用户数
    THROTTLE_SECONDS = 5  # 5秒内只能访问xx次
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}   # 允许的文件上传格式
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 允许的文件大小
    UPLOAD_FILE_KEY = "media"


class DefaultConfig(BaseConfig):
    MEDIA_DIR = os.path.join(os.getcwd(), "media", "images")
    MEDIA_URL = "/media/images"
