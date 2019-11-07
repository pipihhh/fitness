from flask import Flask
from apps import user, course, files
from flask_restful import Api
from conf.default import DefaultConfig
from apps.main.handler import before_request


def create_app():
    app = Flask(__name__, static_url_path=DefaultConfig.MEDIA_URL, static_folder=DefaultConfig.MEDIA_DIR)
    app.config.from_object(DefaultConfig)
    app.before_request_funcs.setdefault(None, []).append(before_request.jwt_handler)  # 用源码的形式给app添加before request
    api = Api(app)
    api.add_resource(user.user.User, "/api/user")
    api.add_resource(user.user_list.UserList, "/api/user_list")
    api.add_resource(course.course.Course, "/api/course")
    api.add_resource(course.action.Action, "/api/action")
    api.add_resource(files.file.File, "/api/upload")
    return app
