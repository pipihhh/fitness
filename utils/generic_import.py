from bs4 import BeautifulSoup
from flask import request, g, current_app, jsonify
from flask_restful import Resource, reqparse
from general.response import Response
from general.sql_map import SelectMap
from general.db_pool import fetchall_dict
from general.exception import UserDoesNotExistException
from utils.error_handler import init_key_error_handler
from utils.general_object import GeneralObject
