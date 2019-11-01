from flask import Flask
from apps.index import ix
from apps.login import log


def create_app():
    app = Flask(__name__)
    app.register_blueprint(ix)
    app.register_blueprint(log)
    return app
