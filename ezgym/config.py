"""应用配置。

全部机密走环境变量（配合 python-dotenv 从 .env 加载）；业务常量集中在此，
供各域直接 `current_app.config[...]` 读取。
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

# import 时加载 .env（若存在）。不覆盖已存在的进程环境变量。
load_dotenv()

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """基类：公共默认值 + 业务常量。"""

    # ---- Flask / Session ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-change-me")
    # 验证码有效期（秒），沿用旧 PERMANENT_SESSION_LIFETIME 语义
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=100)

    # ---- SQLAlchemy ----
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost/ezgym?charset=utf8mb4",
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ---- JWT (flask-jwt-extended) ----
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-insecure-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 24 * 60 * 60))
    )

    # ---- 密码哈希 ----
    BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", 12))

    # ---- 分页 ----
    PAGE_SIZE = 9  # 每页条数（沿用旧 PAGE_OFFSET）
    MAX_PAGE_SIZE = 100

    # ---- 验证码 ----
    AUTH_CODE_LENGTH = 5
    AUTH_CODE_WIDTH = 200
    AUTH_CODE_HEIGHT = 50
    AUTH_CODE_SESSION_KEY = "auth_code"

    # ---- 邮件（找回密码）----
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.163.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 465))
    MAIL_USE_SSL = _bool("MAIL_USE_SSL", True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_SENDER = os.environ.get("MAIL_SENDER") or os.environ.get("MAIL_USERNAME", "")
    MAIL_TITLE = "ezgym 论坛密码找回"
    BACK_PASSWORD_EXP = 30 * 60  # 找回密码链接有效期（秒）

    # ---- 前端 / CORS ----
    USER_HOST = os.environ.get("USER_HOST", "http://127.0.0.1:8080")

    # ---- 媒体文件上传 ----
    MEDIA_DIR = os.environ.get("MEDIA_DIR") or os.path.join(_BASE_DIR, "media", "images")
    MEDIA_URL = os.environ.get("MEDIA_URL", "/media/images")
    UPLOAD_FILE_KEY = "media"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6 MB

    # ---- 限流 (flask-limiter) ----
    RATELIMIT_HEADERS_ENABLED = True

    # ---- 杂项业务常量 ----
    TITLE_LENGTH = 10  # 从 challenge 内容截取标题的长度
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    # 内存 SQLite；StaticPool + check_same_thread 让 create_all 建的表在整个测试
    # 生命周期内共享同一连接（否则内存库随连接销毁而丢表）。
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
    }
    BCRYPT_ROUNDS = 4  # 加速测试
    # 关闭限流干扰单测
    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name: str | None = None):
    """按名称解析配置类；缺省读环境变量 FLASK_CONFIG，再退化到 default。"""
    if not name:
        name = os.environ.get("FLASK_CONFIG", "default")
    return _CONFIG_MAP.get(name, DevelopmentConfig)
