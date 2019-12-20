import hashlib
import functools
from flask import request, jsonify, current_app
from general.response import Response
from conf.code import THROTTLE_ERROR


def idempotent(func):
    """
    此装饰器是实现该请求幂等的装饰器，使用此装饰器的请求必须携带token等
    防止表单重复提交等问题，如果重复提交则返回一个400 请求正在处理
    按理说此装饰器应放在所有装饰器的最上面
    """
    content_set = set()

    @functools.wraps(func)
    def inner(*args, **kwargs):
        response = Response()
        content = f"{request.url}:{request.remote_addr}"
        md5 = hashlib.md5(current_app.config["SALT"].encode(current_app.config["DB_CHARSET"]))
        md5.update(content.encode(current_app.config["DB_CHARSET"]))
        val = md5.hexdigest()
        if val in content_set:
            response.code = THROTTLE_ERROR
            response.errno = 1
            response.data = {"msg": "请求正在处理中"}
            return jsonify(response.dict_data)
        content_set.add(val)
        ret = func(*args, **kwargs)
        content_set.remove(val)
        return ret
    return inner
