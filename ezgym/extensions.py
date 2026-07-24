"""Flask 扩展单例（未绑定 app）。

在此实例化，create_app() 里统一 init_app。各域只从这里 import，
避免循环依赖与多实例。
"""
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
limiter = Limiter(key_func=get_remote_address)
cors = CORS()
