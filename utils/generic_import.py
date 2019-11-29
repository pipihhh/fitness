from bs4 import BeautifulSoup
from flask import request, g, current_app, jsonify
from flask_restful import Resource, reqparse
from conf.permission import ADMIN, NORMAL, permission_valid
from conf.code import FORMAT_ERROR
from general.response import Response
from general.sql_map import SelectMap
from general.db_pool import fetchall_dict
from general.vaild import BaseValid
from general.exception import UserDoesNotExistException, InvalidArgumentException
from utils.error_handler import init_key_error_handler, init_error_message
from utils.general_object import GeneralObject, create_cmp_with_class
