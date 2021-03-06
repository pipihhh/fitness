from flask import request, jsonify, g, current_app
from utils.secert import *
from general.exception import TokenTimeOutException, IllegalTokenException
from general.response import Response
from general.db_pool import pool, get_one
from general.sql_map import SelectMap
from conf.code import *
import datetime


def jwt_handler():
    """
    json web token的处理函数，如果携带了token 则处理 否则略
    :return:
    """
    if request.is_json:
        token = request.json.get("token")
    elif request.method != "GET":
        token = request.form.get("token")
    else:
        token = request.args.get("token")
    if token is not None:
        response = Response()
        try:
            header, payload, signature = token.split(".")
            header = decode_base64(header)
            payload = decode_base64(payload)
            payload_handler(payload)
            alg = header_handler(header)
            signature_handler(header, payload, signature, alg)
        except TokenTimeOutException as e:
            response.code = PERMISSION_ERROR
            response.errno = 1
            response.data = {"msg": str(e)}
        except (KeyError, IndexError, IllegalTokenException) as e:
            response.code = FORMAT_ERROR
            response.errno = 1
            response.data = {"msg": "错误的token:" + str(e)}
        except ValueError:
            response.code = FORMAT_ERROR
            response.errno = 1
            response.data = {
                "msg": "token格式错误"
            }
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
    exp = datetime.datetime.strptime(exp, current_app.config["DATE_FORMAT"])
    if now > exp:
        raise TokenTimeOutException("Token已失效")
    _id = payload["id"]
    permission = payload["permission"]
    password = payload["password"]
    connection = pool.connection()
    cursor = connection.cursor()
    user = get_one(cursor, SelectMap.user_valid_by_id, [_id, ])
    if user[1] != password:
        raise TokenTimeOutException("Token已失效")
    setattr(request, "user", {"id": _id, "permission": permission})
    setattr(g, "user", {"id": _id, "permission": permission})


def header_handler(header):
    typ = header["typ"]
    alg = header["alg"]
    if typ != current_app.config["JWT_TYPE"] or alg != current_app.config["JWT_ALG"]:
        raise IllegalTokenException("非法的Token!")
    return alg


def signature_handler(header, payload, signature, alg):
    mock = get_jwt(
        encode_base64(json.dumps(header)), encode_base64(json.dumps(payload)), alg
    ).split(".")[-1]
    if mock != signature:
        raise IllegalTokenException("非法的Token!")
