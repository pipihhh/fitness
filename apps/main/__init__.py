import datetime
from flask import Flask, current_app
from flask.json import JSONEncoder
from apps import user, course, files, challenge, blog, comment, search
from flask_restful import Api
from conf.default import DefaultConfig
from apps.main.handler import before_request, after_request


def create_app():
    app = Flask(__name__, static_url_path=DefaultConfig.MEDIA_URL, static_folder=DefaultConfig.MEDIA_DIR)
    app.config.from_object(DefaultConfig)
    app.before_request_funcs.setdefault(None, []).append(before_request.jwt_handler)  # 用源码的形式给app添加before request
    app.after_request_funcs.setdefault(None, []).append(after_request.init_cors)  # 添加跨域相关的配置信息
    app.json_encoder = FitnessJSONEncoder   # 指定自定义的json解析器 此解析器继承了flask的默认json解析器
    api = Api(app)
    api.add_resource(user.user.User, "/api/user")
    api.add_resource(user.user_list.UserList, "/api/user_list")
    api.add_resource(course.course.Course, "/api/course")
    api.add_resource(course.action.Action, "/api/action")
    api.add_resource(files.file.File, "/api/file")
    api.add_resource(user.auth_code.AuthCode, "/api/auth_code")
    api.add_resource(challenge.challenge.Challenge, "/api/challenge")
    api.add_resource(blog.blog.Blog, "/api/blog")
    api.add_resource(blog.blog_list.BlogList, "/api/blog_list")
    api.add_resource(blog.upper.Upper, "/api/upper")
    api.add_resource(comment.comment.Comment, "/api/comment")
    api.add_resource(course.course_list.CourseList, "/api/course_list")
    api.add_resource(course.action_list.ActionList, "/api/action_list")
    api.add_resource(challenge.challenge_list.ChallengeList, "/api/challenge_list")
    api.add_resource(search.time_window.TimeWindow, "/api/time")
    api.add_resource(search.searcher.Searcher, "/api/search")
    return app


class FitnessJSONEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime(current_app.config["DATE_FORMAT"])
        if isinstance(o, datetime.date):
            return o.isoformat()
        else:
            return JSONEncoder.default(self, o)
