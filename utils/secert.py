import base64
from flask import current_app
import hmac
import json


def encode_base64(string):
    charset = current_app.config["DB_CHARSET"]
    return base64.b64encode(string.encode(charset)).decode(charset)


def decode_base64(string):
    charset = current_app.config["DB_CHARSET"]
    d = base64.b64decode(string).decode(charset)
    return json.loads(d)


def get_jwt(header, payload, alg="sha256"):
    string = "".join([header, ".", payload, "."])
    salt = current_app.config["SALT"]
    charset = current_app.config["DB_CHARSET"]
    mac = hmac.new(salt.encode(charset), alg.encode(charset))
    mac.update(string.encode(charset))
    string += mac.hexdigest()
    return string
