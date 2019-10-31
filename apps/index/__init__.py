from flask.blueprints import Blueprint
import importlib


ix = Blueprint("index", __name__, template_folder="./templates", static_folder="./static")
importlib.import_module("apps.index.views.index")
