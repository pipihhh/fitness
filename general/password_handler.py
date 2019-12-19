from flask import current_app
import hashlib


def md5(password):
    charset = current_app.config["DB_CHARSET"]
    m = hashlib.md5(current_app.config["SALT"].encode(charset))
    if isinstance(password, bytes):
        m.update(password)
    else:
        m.update(password.encode(charset))
    return m.hexdigest()
