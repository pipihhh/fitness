import datetime
from flask import current_app


def get_exp_str():
    exp = current_app.config["EXP_MIN"]
    date_format = current_app.config["DATE_FORMAT"]
    delta = datetime.timedelta(minutes=exp)
    return datetime.datetime.strftime(datetime.datetime.now() + delta, date_format)


def get_now():
    return datetime.datetime.strftime(datetime.datetime.now(), current_app.config["DATE_FORMAT"])
