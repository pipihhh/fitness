from functools import wraps
from flask import g, jsonify
from general.response import Response
from conf.code import PERMISSION_ERROR


__all__ = ("ADMIN", "NORMAL", "permission_valid")


ADMIN = 0b11111111  # 管理员权限  255
NORMAL = 0b00000001  # 普通的用户权限 只有修改自己的信息的权限 1


def permission_valid(permission):
    """
    装饰器，校验权限，想要校验权限的方法前加装饰器
    :param permission: 权限的值
    :return: 如果符合权限则执行方法，否则返回一个json
    """
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            response = Response()
            user_permission = getattr(g, "user", {}).get("permission", 0)
            if permission & user_permission == permission:
                return func(*args, **kwargs)
            else:
                response.code = PERMISSION_ERROR
                response.errno = 1
                response.data = {"msg": "权限不足"}
                return jsonify(response.dict_data)
        return inner
    return wrapper
