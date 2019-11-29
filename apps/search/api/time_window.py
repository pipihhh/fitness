import datetime
from utils.generic_import import *


class TimeWindow(Resource):

    @permission_valid(ADMIN)
    def get(self):
        """
        此方法传4个参数 token  tag start_time end_time
        其中tag表示你想要调用的具体的接口 如user
        start_time和end_time的格式为 2019-01-01 这种 不可配置
        此接口返回值不包含end_time对应日期 但是包含start_time对应日期 顾头不顾尾
        :return:
        """
        response = Response()
        data = TimeValid(request.args)
        response.data = data.valid_data()
        if response.data != {}:
            response.errno = len(response.data)
            response.code = FORMAT_ERROR
            return jsonify(response.dict_data)
        try:
            tag = request.args["tag"]
            func = getattr(self, f"_{tag}_window")
            func(response, data.clean_data)
        except KeyError:
            init_error_message(response, message="找不到入参:tag")
        except ValueError:
            init_error_message(response, message="错误的时间格式")
        except AttributeError:
            init_error_message(response, message="找不到tag对应的接口")
        except Exception as e:
            init_error_message(response, message=str(e))
        return jsonify(response.dict_data)

    def _user_window(self, response, data_dict):
        """
        此方法根据时间窗口返回用户相关的数据 时间的格式为 yy-mm-dd 必须带0 如2019-01-01 不可以是2019-1-1
        此方法返回的用户包含start_time 不包含end_time当日
        :param response:
        :return:
        """
        start_window = data_dict["start_time"]
        end_window = data_dict["end_time"]
        user_list = fetchall_dict(SelectMap.user_generic, (start_window, end_window), GeneralObject)
        user_list.sort(key=lambda u: u.create_time)
        ret = []
        index = 0
        _range = (end_window - start_window).days
        for day in range(_range):
            s = start_window + datetime.timedelta(day)
            e = s + datetime.timedelta(hours=23, minutes=59, seconds=59)
            count = 0
            while index < len(user_list):
                if s <= user_list[index].create_time <= e:
                    count += 1
                    index += 1
                else:
                    break
            ret.append({
                "node": datetime.date(s.year, s.month, s.day),
                "count": count
            })
        response.data = {
            "time_window": ret,
            "count": len(ret),
        }


class TimeValid(BaseValid):
    def valid(self):
        start_time = datetime.datetime.strptime(getattr(self, "start_time"), "%Y-%m-%d")
        end_time = datetime.datetime.strptime(getattr(self, "end_time"), "%Y-%m-%d")
        delta = datetime.timedelta(days=30)
        if start_time >= end_time:
            raise InvalidArgumentException("开始时间大于结束时间")
        if end_time - start_time > delta:
            raise InvalidArgumentException("超过30天")
        setattr(self, "start_time", start_time)
        setattr(self, "end_time", end_time)
