import os
from flask import request, current_app, jsonify
from flask_restful import Resource
from utils.file_utils import is_safe, generate_filename, get_suffix
from utils.idempotent_request import idempotent
from utils.general_object import GeneralObject
from general.password_handler import md5
from general.db_pool import fetchone_dict, execute_sql
from general.sql_map import SelectMap, InsertMap
from general.response import Response
from conf.code import FORMAT_ERROR
from conf.permission import permission_valid, NORMAL


class File(Resource):

    @idempotent
    @permission_valid(NORMAL)
    def post(self):
        """
        文件上传的接口，可以上传多个文件
        :return:
        """
        files = request.files.getlist(current_app.config["UPLOAD_FILE_KEY"])
        response = Response()
        media_url = current_app.config["MEDIA_URL"]
        media_dir = current_app.config["MEDIA_DIR"]
        err_list = []
        suffix_list = []
        for f in files:
            if is_safe(f.filename):
                suffix_list.append(get_suffix(f.filename))
                continue
            err_list.append(f.filename)
        if err_list:
            response.errno = len(err_list)
            response.code = FORMAT_ERROR
            response.data = {
                "msg": "错误的文件类型:" + ",".join(err_list)
            }
            return jsonify(response.dict_data)
        file_url = []
        for index, f in enumerate(files):
            file_name = generate_filename() + "." + suffix_list[index]
            path = os.path.join(media_dir, file_name)
            file_name = self._save(f, path, file_name)
            file_url.append({
                "url": os.path.join(media_url, file_name),
                "filename": file_name
            })
        response.data = {"msg": file_url}
        return jsonify(response.dict_data)

    def _save(self, file, path, filename):
        buf = file.stream.read()
        md5_key = md5(buf)
        file_map = fetchone_dict(SelectMap.file_map, (md5_key, ), GeneralObject)
        if file_map:
            return file_map.filename
        file.save(path)
        with open(path, "wb") as new_f:
            new_f.write(buf)
        execute_sql(InsertMap.file_map, (filename, md5_key), True)
        return filename
