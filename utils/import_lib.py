import importlib


def register(string):
    importlib.import_module(string)
