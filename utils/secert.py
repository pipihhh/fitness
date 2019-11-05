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


def get_jwt(header, payload):
    string = "".join([header, ".", payload, "."])
    salt = current_app.config["SALT"]
    charset = current_app.config["DB_CHARSET"]
    mac = hmac.new(salt.encode(charset), "sha256".encode(charset))
    mac.update(string.encode(charset))
    string += mac.hexdigest()
    return string


if __name__ == '__main__':
    header = encode_base64(json.dumps({"typ": "JWT", "alg": "HS256"}))
    payload = encode_base64(json.dumps({"exp": "2019-12-30 00:00:00", "id": 1, "permission": 256}))
    jwt = get_jwt(header, payload)
    print(jwt)
