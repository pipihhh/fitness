from copy import deepcopy


class BaseValid(object):
    def __init__(self, kwargs=None):
        self._err_map = {}
        self._valid_flag = None
        self._copy_flag = False
        self._cache = {}
        if kwargs is not None:
            add_arg(self, kwargs)

    def valid(self):
        pass

    def _filter(self):
        try:
            self.valid()
        except Exception as e:
            self._err_map["all"] = str(e)
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

    @property
    def clean_data(self):
        if self._valid_flag is None:
            self._filter()
        if self._copy_flag is False:
            self._cache = deepcopy(self.__dict__)
            self._cache.pop("_err_map")
            self._cache.pop("_valid_flag")
            self._cache.pop("_copy_flag")
            self._cache.pop("_cache")
            self._copy_flag = True
        return self._cache


def add_arg(obj, args):
    for arg, val in args.items():
        if not hasattr(obj, arg) and val is not None:
            setattr(obj, arg, val)
