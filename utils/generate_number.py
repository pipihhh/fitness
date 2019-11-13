import uuid


def generate_number(length):
    """
    生成唯一的uuid 根据传入的长度
    主要用于post请求时
    :param length:
    :return:
    """
    return str(uuid.uuid4())[:length]
