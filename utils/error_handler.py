from conf.code import *


def init_key_error_handler(response, e, message="错误的入参格式"):
    response.code = FORMAT_ERROR
    response.errno = 1
    response.data = {"msg": message + str(e)}


def init_error_message(response, code=FORMAT_ERROR, message="错误的入参"):
    response.code = code
    response.errno += 1
    if response.data is None:
        response.data = {"msg:1": message}
    else:
        response.data.update({_get_key(response.data): message})


def _get_key(obj):
    count = 1
    for key in obj:
        key = int(key.split(":")[-1])
        if key > count:
            count = key
    return f"msg:{count+1}"
