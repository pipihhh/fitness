"""统一响应封装。

保留旧 body 契约 {"errno": int, "code": int, "data": ...}（errno=0 成功），
但与旧实现不同：HTTP 状态码不再恒为 200，而是与业务 code 对齐（修 CR）。

flask-restful 的 Resource 方法可直接 `return ok(data)`，返回 (body, http_status)
二元组即被正确序列化并设置状态码。
"""
from typing import Any

__all__ = ["make_body", "ok"]


def make_body(data: Any = None, code: int = 200, errno: int = 0) -> dict:
    """构造响应 body（不含 HTTP 状态码）。"""
    return {"errno": errno, "code": code, "data": data}


def ok(data: Any = None, http_status: int = 200) -> tuple[dict, int]:
    """成功响应：body 的 code 与 HTTP status 对齐，errno=0。

    flask-restful 识别 (dict, status) 元组并据此设置响应状态码。
    """
    return make_body(data=data, code=http_status, errno=0), http_status
