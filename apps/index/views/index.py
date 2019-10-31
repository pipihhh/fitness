from apps.index import ix
from flask import render_template


@ix.route("/index")
def index():
    return render_template("index.html")
