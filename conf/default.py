import os


class BaseConfig(object):
    """
    默认的配置类，包括数据库连接池的配置和密码加盐的配置
    还有是否是调试环境
    """
    SECRET_KEY = "jsjkfhaskjhdjkashkfj"  # 加密session时候使用的秘钥
    PERMANENT_SESSION_LIFETIME = 100   # 设置验证码的超时时间 超过此时间后的验证码无效
    USER_HOST = "http://127.0.0.1:8080"  # 前端的域名 localhost和127不同
    DB_NAME = "ezgym"
    DB_USER = "root"
    DB_PASSWORD = "root"
    DB_PORT = 3306
    DB_HOST = "localhost"
    DB_CHARSET = "utf8"  # 设置当前系统的所有编码 包括数据库的编码
    DEBUG = False   # 设置此时为调试模式
    SALT = "jsjkfhaskjhdjkashkfj"  # 各种加密时候所加的盐 包含密码的加密 默认无需修改
    JWT_TYPE = "JWT"   # token使用的协议 默认只有这个
    JWT_ALG = "sha256"  # token的加密算法
    EXP_MIN = 24 * 60    # token的失效时间 分钟为单位
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # 时间的格式,如2019-11-11 11:11:11
    PAGE_OFFSET = 9   # 分页相关，每页显示的用户数
    THROTTLE_SECONDS = 5  # 5秒内只能访问xx次
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', "JPG", "JPEG", "PNG"}   # 允许的文件上传格式
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 允许的文件大小 此为6MB
    UPLOAD_FILE_KEY = "media"   # 配置上传文件时候 文件value对应的key
    AUTH_CODE_LENGTH = 5     # 配置验证码的长度
    AUTH_CODE_WIDTH = 200    # 配置验证码图片的width
    AUTH_CODE_HEIGHT = 50      # 配置验证码图片的height
    AUTH_CODE_BG_COLOR = "#F8F8FF"  # 16进制的方式配置颜色 或者支持的颜色英文也可
    AUTH_CODE_FONT = "Menlo.ttc"   # 配置验证码文字的字体 详见/System/Library/Fonts
    AUTH_CODE_FONTSIZE = 16  # 配置验证码文字的字体大小
    AUTH_CODE_LINES = 3  # 配置干扰线的条数
    AUTH_CODE_SESSION_KEY = "auth_code"  # 验证码通过session在获取图片的时候发给浏览器 并且在收到验证码的时候比对 此时的session key
    TITLE_LENGTH = 10   # 取挑战的标题的时候 取内容的长度值xxx作为标题
    BACK_PASSWORD_EXP = 30 * 60  # 找回密码的邮箱验证时长 单位 秒
    EMAIL_HOST_SERVER = "smtp.163.com"
    EMAIL_SENDER = "ezgym_bbs@163.com"
    EMAIL_SENDER_CODE = "ljyljh123"
    EMAIL_TITLE = "ezgym论坛密码找回"
    CALLBACK_URL = ""   # 密码找回的回调页面 此页面会发给用户的邮箱
    RECEIVER_NICK = "尊敬的用户"  # 接收者别名


class DefaultConfig(BaseConfig):
    MEDIA_DIR = os.path.join(os.getcwd(), "media", "images")  # 媒体文件所在的目录
    MEDIA_URL = "/media/images"   # 媒体文件的URL
