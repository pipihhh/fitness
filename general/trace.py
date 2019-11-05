import traceback


def trace():
    s = ""
    for line in traceback.format_stack():
        s += line
    return s
