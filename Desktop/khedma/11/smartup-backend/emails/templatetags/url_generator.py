from django import template

from settings.settings import BACKEND_URL

register = template.Library()


@register.filter(name="url_generator")
def url_generator(value):
    return f"{BACKEND_URL}{value}"
