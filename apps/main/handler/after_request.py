def init_cors(response):
    """
    跨域的一些配置 允许跨域
    :param response:
    :return:
    """
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers",
                         "User-Agent,Origin,Cache-Control,Content-type,Date,Server,withCredentials,AccessToken")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, HEAD")
    return response
