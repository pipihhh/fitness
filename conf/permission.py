from functools import wraps
from flask import g, jsonify, session, current_app, request
from general.response import Response
from general.exception import InvalidArgumentException
from conf.code import PERMISSION_ERROR, FORMAT_ERROR


__all__ = ("ADMIN", "NORMAL", "permission_valid", "auth_code_valid")


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


def auth_code_valid(func):
    """
    使用此装饰器的请求中，在其请求的session中必须携带了二维码验证的key 否则会报异常
    且在请求的ajax中必须携带以配置好的key为键 验证码为value的字符串格式的验证码
    :param func:
    :return:
    """

    @wraps(func)
    def inner(*args, **kwargs):
        response = Response()
        key = current_app.config["AUTH_CODE_SESSION_KEY"]
        try:
            auth_code = session[key].lower()
            code = request.json[key].lower()
            if code != auth_code:
                raise InvalidArgumentException()
            ret = func(*args, **kwargs)
            session.clear()
            return ret
        except KeyError:
            response.code = FORMAT_ERROR
            response.errno = 1
            response.msg = {"msg": "无效的验证码"}
        except InvalidArgumentException:
            response.code = FORMAT_ERROR
            response.errno = 1
            response.msg = {"msg": "验证码校验错误"}
        return jsonify(response.dict_data)
    return inner
