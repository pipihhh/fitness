class GeneralObject(object):
    def __init__(self):
        object.__setattr__(self, "_items", {})

    def __getattr__(self, item):
        return self._items.get(item)

    def __setattr__(self, key, value):
        self._items[key] = value

    def __str__(self):
        return f"<General:{object.__getattribute__(self, '_items')}>"

    @property
    def data(self):
        return object.__getattribute__(self, '_items')


def create_cmp_with_class(cmp):
    if callable(cmp):
        return type(
            cmp.__name__ + "_class", (GeneralObject,), {
                "__lt__": cmp
            }
        )
    else:
        raise ValueError("%s is not callable" % cmp.__name__)
