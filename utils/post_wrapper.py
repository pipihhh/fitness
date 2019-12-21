from utils.post_template import post


def generic_template(valid_class, parse, template_class):
    template = template_class()
    resp = post(valid_class, parse, template)
    return (False, resp) if resp else (True, template)
