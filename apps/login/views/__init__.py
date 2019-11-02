from apps.login import log
from flask import render_template


@log.route("/login")
def login():
    return render_template("login.html")


@log.route("/register")
def register():
    return render_template("register.html")
