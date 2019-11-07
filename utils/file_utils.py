import time
import uuid
import hashlib
from flask import current_app


def is_safe(filename):
    suffix = current_app.config["ALLOWED_EXTENSIONS"]
    names = filename.split(".")
    return len(names) >= 2 and names[-1] in suffix


def generate_filename():
    md5 = hashlib.md5(current_app.config["SALT"].encode(current_app.config["DB_CHARSET"]))
    filename = str(time.time()) + str(uuid.uuid4())
    md5.update(filename.encode(current_app.config["DB_CHARSET"]))
    return md5.hexdigest()


def get_suffix(filename):
    return filename.rsplit(".", 2)[-1]
