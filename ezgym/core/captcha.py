"""图形验证码。

用 captcha 库生成图片 + 文本（替代旧的手绘 PIL 逻辑），并提供基于 session 的
存取 helper：generate 后 store，校验后 clear（一次性）。
"""
import random
import string

from captcha.image import ImageCaptcha
from flask import current_app, session

__all__ = ["generate", "store_code", "verify_code"]


def _random_text(length: int) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def generate() -> tuple[str, bytes]:
    """生成验证码，返回 (text, png_bytes)。text 大写便于不区分大小写比对。"""
    length = current_app.config.get("AUTH_CODE_LENGTH", 5)
    width = current_app.config.get("AUTH_CODE_WIDTH", 200)
    height = current_app.config.get("AUTH_CODE_HEIGHT", 50)
    text = _random_text(length)
    image = ImageCaptcha(width=width, height=height)
    png_bytes = image.generate(text).getvalue()
    return text, png_bytes


def _session_key() -> str:
    return current_app.config.get("AUTH_CODE_SESSION_KEY", "auth_code")


def store_code(text: str) -> None:
    """把验证码文本存入 session（大写归一）。"""
    session[_session_key()] = text.upper()


def verify_code(candidate: str | None) -> bool:
    """校验并清除（一次性）。不区分大小写。"""
    key = _session_key()
    stored = session.get(key)
    session.pop(key, None)
    if not stored or not candidate:
        return False
    return stored.upper() == candidate.upper()
