from flask import request


def jwt_handler():
    token = request.json.get("token", "")
