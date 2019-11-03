from flask.blueprints import Blueprint
from utils.import_lib import register


ix = Blueprint("index", __name__,
               template_folder="./templates",
               static_folder="./static",
               static_url_path="/index/static/")
register("apps.index.views")
