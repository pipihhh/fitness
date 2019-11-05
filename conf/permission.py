from functools import wraps
from flask import g, jsonify
from general.response import Response


ADMIN = 0o11111111  # 管理员权限
NORMAL = 0o0000001  # 普通的用户权限 只有修改自己的信息的权限


def permission_valid(permission):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            response = Response()
            user_permission = getattr(g, "user", {}).get("permission", 0)
            if permission & user_permission == permission:
                return func(*args, **kwargs)
            else:
                response.code = 403
                response.errno = 1
                response.data = {"msg": "权限不足"}
                return jsonify(response.dict_data)
        return inner
    return wrapper
