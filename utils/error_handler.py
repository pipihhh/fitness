from conf.code import *


def init_key_error_handler(response, e, message="错误的入参格式"):
    response.code = FORMAT_ERROR
    response.errno = 1
    response.data = {"msg": message + str(e)}
