from flask import Flask
from apps.index import ix


def create_app():
    app = Flask(__name__)
    app.register_blueprint(ix)
    return app
