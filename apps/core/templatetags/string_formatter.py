from django.template import Library
from django.utils.translation import gettext

register = Library()


@register.filter
def translate_title(title):
    if title is None:
        return ""
    try:
        return gettext(" ".join(x.capitalize() or "_" for x in title.split("_")))
    except Exception:
        return title


@register.filter
def int_divide(value, arg):
    if type(value) != int or type(arg) != int or arg == 0:
        return value
    return int(value) // int(arg)
