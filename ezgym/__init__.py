"""ezgym 应用工厂。

create_app 负责：选配置 -> init 扩展 -> 注册 error handler -> 建 flask-restful Api
-> 遍历各域 resources.register(api) -> 注册 CLI 与健康检查。

关于 flask-restful 与 Flask 3：flask-restful 0.3.10 的默认 JSON 表示用的是标准库
json.dumps（不走 app.json provider），datetime 会报错。这里把 application/json
表示替换为走 app.json.dumps 的实现，让自定义 JSONProvider（ISO datetime）对
flask-restful 的响应同样生效——从根因统一序列化，而非降级 Flask。
"""
from datetime import date, datetime

from flask import Flask, current_app, make_response
from flask.json.provider import DefaultJSONProvider

from ezgym.config import get_config
from ezgym.core.errors import register_error_handlers
from ezgym.core.response import make_body
from ezgym.core.security import register_jwt_error_handlers
from ezgym.extensions import cors, db, jwt, limiter, ma, migrate

__all__ = ["create_app"]

# 显式列出全部域的 register 入口，避免各域 agent 改动本文件产生合并冲突。
_DOMAIN_MODULES = [
    "ezgym.domains.identity.resources",
    "ezgym.domains.course.resources",
    "ezgym.domains.challenge.resources",
    "ezgym.domains.content.resources",
    "ezgym.domains.interaction.resources",
    "ezgym.domains.social.resources",
    "ezgym.support.search.resources",
    "ezgym.support.notification.resources",
    "ezgym.support.media.resources",
]

# 所有 model 模块，import 即向 db.metadata 注册（供 create_all / migrate 感知）。
_MODEL_MODULES = [
    "ezgym.domains.identity.models",
    "ezgym.domains.course.models",
    "ezgym.domains.challenge.models",
    "ezgym.domains.content.models",
    "ezgym.domains.interaction.models",
    "ezgym.domains.social.models",
    "ezgym.support.media.models",
]


class EzgymJSONProvider(DefaultJSONProvider):
    """自定义 JSON provider：datetime/date 序列化为 ISO 字符串（替代旧 json_encoder）。"""

    @staticmethod
    def default(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return DefaultJSONProvider.default(obj)


def _import_all_models() -> None:
    import importlib

    for mod in _MODEL_MODULES:
        importlib.import_module(mod)


def _restful_output_json(data, code, headers=None):
    """flask-restful 的 application/json 表示，改走 app.json 序列化。"""
    dumped = current_app.json.dumps(data)
    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    resp.headers["Content-Type"] = "application/json"
    return resp


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # 自定义 JSON provider（Flask 3 的 app.json 机制，取代已移除的 json_encoder）
    app.json = EzgymJSONProvider(app)

    # 确保所有模型被 import 并注册到 metadata
    _import_all_models()

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    register_jwt_error_handlers(jwt)
    ma.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config.get("USER_HOST", "*")}},
        supports_credentials=True,
    )

    # 统一 error handler
    register_error_handlers(app)

    # flask-restful Api（绑定 app），并接管 JSON 序列化
    from flask_restful import Api

    api = Api(app, catch_all_404s=False)
    api.representations["application/json"] = _restful_output_json

    # 健康检查（工厂内直接注册，独立于各域）
    @app.get("/api/health")
    def _health():
        return make_body(data={"status": "ok"}, code=200, errno=0), 200

    # 遍历各域注册路由
    import importlib

    for mod_path in _DOMAIN_MODULES:
        module = importlib.import_module(mod_path)
        register = getattr(module, "register", None)
        if callable(register):
            register(api)

    # CLI 命令
    from ezgym.cli import register_cli

    register_cli(app)

    return app
