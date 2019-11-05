from flask import Flask
from apps.user import user
from flask_restful import Api
from conf.default import DefaultConfig
from apps.main.handler import before_request


def create_app():
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)
    app.before_request_funcs.setdefault(None, []).append(before_request.jwt_handler)  # 用源码的形式给app添加before request
    api = Api(app)
    api.add_resource(user.User, "/api/user")
    return app
