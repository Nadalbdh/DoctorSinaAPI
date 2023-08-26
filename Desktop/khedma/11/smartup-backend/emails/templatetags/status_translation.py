from django import template

from backend.enum import RequestStatus

register = template.Library()


@register.filter(name="status_translate")
def status_translate(value):
    # TODO This is useful, maybe consider moving it somewhere where it's more
    # discoverable
    return {
        status: translation for (status, translation) in RequestStatus.get_choices()
    }.get(value)


@register.filter(name="status_translate")
def status_translate(value):
    """
    Args:
        value (string): a single or comma separated status in english
        eg: "INVALID" or "PROCESSING,INVALID"
    """
    if "," not in value:
        arabic = {
            status: translation
            for (status, translation) in RequestStatus.get_choices_complaints()
        }.get(value)
        if arabic != None:
            return arabic
        return ""

    return (
        status_translate(value[: value.index(",")])
        + " "
        + status_translate(value[value.index(",") + 1 :])
    )
