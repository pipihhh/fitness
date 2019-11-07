from general.response import Response
from conf.code import FORMAT_ERROR


def post(valid_class, parse, template):
    valid = valid_class(parse.parse_args())
    err_map = valid.valid_data()
    if err_map:
        response = Response()
        response.data = err_map
        response.errno = len(err_map)
        response.code = FORMAT_ERROR
        return response
    clean_data = valid.clean_data
    for key in template.__dict__:
        if key in clean_data:
            setattr(template, key, clean_data[key])
