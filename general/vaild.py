class BaseValid(object):
    def __init__(self):
        self._err_map = {}
        self._valid_flag = None

    def _filter(self):
        for arg_name in self.__dict__:
            func_name = arg_name + "_valid"
            if hasattr(self, func_name):
                try:
                    getattr(self, func_name)(self.__dict__[arg_name])
                except Exception as e:
                    self._err_map[arg_name] = str(e)
        self._valid_flag = True

    def valid_data(self):
        if self._valid_flag is None:
            self._filter()
        return self._err_map


def add_arg(obj, args):
    for arg, val in args.items():
        if not hasattr(obj, arg):
            setattr(obj, arg, val)
