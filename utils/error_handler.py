from conf.code import *


def init_key_error_handler(response, e):
    response.code = FORMAT_ERROR
    response.errno = 1
    response.data = {"msg": "错误的入参格式:" + str(e)}
