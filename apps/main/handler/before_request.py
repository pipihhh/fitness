from flask import request, jsonify
from utils.secert import *
from general.exception import TokenTimeOutException, IllegalTokenException
from general.response import Response
from conf.code import *
import datetime


def jwt_handler():
    """
    json web token的处理函数，如果携带了token 则处理 否则略
    :return:
    """
    token = request.json.get("token")
    if token is not None:
        response = Response()
        header, payload, signature = token.split(".")
        header = decode_base64(header)
        payload = decode_base64(payload)
        try:
            payload_handler(payload)
            header_handler(header)
            signature_handler(header, payload, signature)
        except TokenTimeOutException as e:
            response.code = PERMISSION_ERROR
            response.errno = 1
            response.data = {"msg": str(e)}
        except KeyError or IndexError or IllegalTokenException as e:
            response.code = FORMAT_ERROR
            response.errno = 1
            response.data = {"msg": "错误的token"}
        except Exception as e:
            response.code = SERVER_ERROR
            response.errno = 1
            response.data = {"msg": "服务端错误:" + str(e)}
        finally:
            if response.errno > 0:
                if hasattr(request, "user"):
                    delattr(request, "user")
                return jsonify(response.dict_data)


def payload_handler(payload):
    now = datetime.datetime.now()
    exp = payload.get("exp", "1999-12-30 00:00:00")
    exp = datetime.datetime.strptime(exp, "%Y-%m-%d %H:%M:S")
    if now > exp:
        raise TokenTimeOutException("Token已失效")
    _id = payload["id"]
    permission = payload["permission"]
    setattr(request, "user", {"id": _id, "permission": permission})


def header_handler(header):
    typ = header["typ"]
    alg = header["alg"]
    if typ != "JWT" or alg != "HS256":
        raise IllegalTokenException("非法的Token!")


def signature_handler(header, payload, signature):
    mock = get_jwt(encode_base64(json.dumps(header)), encode_base64(json.dumps(payload))).split(".")[-1]
    if mock != signature:
        raise IllegalTokenException("非法的Token!")
