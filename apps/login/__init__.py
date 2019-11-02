from flask.blueprints import Blueprint
from utils.import_lib import register


log = Blueprint("login", __name__, template_folder="./templates", static_folder="./static")
register("apps.login.views")
