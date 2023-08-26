from django import template

from backend.enum import DossierTypes

register = template.Library()


@register.filter(name="dossier_type_translate")
def dossier_type_translate(value):
    return {
        status: translation for (status, translation) in DossierTypes.get_choices()
    }.get(value)
