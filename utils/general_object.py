class GeneralObject(object):
    def __init__(self):
        object.__setattr__(self, "_items", {})

    def __getattr__(self, item):
        return self._items.get(item)

    def __setattr__(self, key, value):
        self._items[key] = value
