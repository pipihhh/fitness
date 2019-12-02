from flask_restful import reqparse
from general.response import Response
from conf.code import FORMAT_ERROR


def post(valid_class, parse, template):
    """
    一些固定的对象的方法模板 多用于post和put
    :param valid_class:
    :param parse:
    :param template:
    :return:
    """
    if isinstance(parse, dict):
        valid = valid_class(parse)
    elif isinstance(parse, reqparse.RequestParser):
        valid = valid_class(parse.parse_args())
    else:
        raise ValueError("parse must be dict or RequestParser")
    err_map = valid.valid_data()
    if err_map:
        response = Response()
        response.data = err_map
        response.errno = len(err_map)
        response.code = FORMAT_ERROR
        return response
    clean_data = valid.clean_data
    # for key in template.__dict__:
    #     if template.__dict__[key] is None:
    #         setattr(template, key, clean_data[key])
    for key in clean_data:
        if not key.startswith("_"):
            setattr(template, key, clean_data[key])
