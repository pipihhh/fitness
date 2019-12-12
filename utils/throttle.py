import time
from functools import wraps
from flask import request, jsonify
from conf.default import DefaultConfig
from general.response import Response
from conf.code import THROTTLE_ERROR


def throttle(times, seconds=None):
    """
    限流器，作为装饰器使用 此限流器 多个方法不共享
    :param times: 限流单位 秒  配置内的秒内的访问次数
    :param seconds: 秒 如果不填默认按照配置THROTTLE_SECONDS来作为秒数
    :return:
    """

    def wrapper(func):
        nonlocal seconds
        nonlocal times
        seconds = seconds or DefaultConfig.THROTTLE_SECONDS
        ip_map = {}

        @wraps(func)
        def inner(*args, **kwargs):
            response = Response()
            ip = request.remote_addr
            if ip not in ip_map:
                ip_map[ip] = _IpStack(times, seconds)
            ret = ip_map[ip].append(time.time())
            if ret:
                return func(*args, **kwargs)
            else:
                response.errno = 1
                response.code = THROTTLE_ERROR
                response.data = {"msg": "请求过于频繁，稍后再试"}
                return jsonify(response.dict_data)

        return inner

    return wrapper


class _IpStack(object):
    """
    一个基于列表实现的自定义的时间节流队列，在append的时候会判断时间是否超时 超时则弹出内部容器的时间
    """
    def __init__(self, size, seconds):
        self._size = 0
        self._max_size = size
        self._container = []
        self._seconds = seconds

    def __len__(self):
        return len(self._container)

    def is_empty(self):
        return self._size == 0

    def is_full(self):
        return self._size == self._max_size

    def append(self, element):
        if self.is_full():
            self._resize()
        if self.is_full():
            return False
        self._container.append(element)
        self._size += 1
        return True

    def _resize(self):
        current_time = time.time()
        while not self.is_empty():
            if self._container[0] + self._seconds < current_time:
                self._container.pop(0)
                self._size -= 1
            else:
                break
