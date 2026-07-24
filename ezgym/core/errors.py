"""领域异常与全局 error handler。

统一把异常转成 {"errno": 1, "code": <http>, "data": <message>} 且设置正确的
HTTP 状态码。业务代码抛 ApiException 子类即可，无需在 Resource 里手写 errno/code。
"""
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from ezgym.core.response import make_body

__all__ = [
    "ApiException",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "Conflict",
    "TooManyRequests",
    "register_error_handlers",
]


class ApiException(Exception):
    """业务异常基类。

    :param message: 给前端的错误信息（放进 body 的 data）
    :param http_status: HTTP 状态码，同时写进 body 的 code
    :param code: 若需与 http_status 不同的业务码，可覆盖
    :param errno: 出错标志，>0 表示失败
    """

    http_status = 400
    errno = 1

    def __init__(self, message="请求错误", http_status=None, code=None, errno=None):
        super().__init__(message)
        self.message = message
        if http_status is not None:
            self.http_status = http_status
        self.code = code if code is not None else self.http_status
        if errno is not None:
            self.errno = errno

    def to_body(self) -> dict:
        return make_body(data=self.message, code=self.code, errno=self.errno)


class BadRequest(ApiException):
    http_status = 400


class Unauthorized(ApiException):
    http_status = 401


class Forbidden(ApiException):
    http_status = 403


class NotFound(ApiException):
    http_status = 404


class Conflict(ApiException):
    http_status = 409


class TooManyRequests(ApiException):
    http_status = 429


def register_error_handlers(app):
    """把各类异常统一转成契约 body + 正确 HTTP 状态码。"""

    @app.errorhandler(ApiException)
    def _handle_api_exception(exc: ApiException):
        return exc.to_body(), exc.http_status

    @app.errorhandler(ValidationError)
    def _handle_validation_error(exc: ValidationError):
        # marshmallow 校验失败 -> 400，data 里带字段级错误
        return make_body(data=exc.messages, code=400, errno=1), 400

    @app.errorhandler(HTTPException)
    def _handle_http_exception(exc: HTTPException):
        status = exc.code or 500
        return make_body(data=exc.description, code=status, errno=1), status

    @app.errorhandler(Exception)
    def _handle_uncaught(exc: Exception):
        # 兜底：未预期异常 -> 500，避免泄漏堆栈给前端
        app.logger.exception("Unhandled exception: %s", exc)
        message = str(exc) if app.debug else "服务器内部错误"
        return make_body(data=message, code=500, errno=1), 500
