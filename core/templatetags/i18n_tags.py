from django import template
from django.utils.translation import get_language

register = template.Library()
from core.translations import t

@register.simple_tag
def tr(text, lang=None):
    """Translate a string using the current session language."""
    lang = lang or get_language()
    return t(text, lang=lang)

@register.simple_tag
def trf(text, lang=None, **kwargs):
    """Translate a string with named interpolation, using the current language."""
    lang = lang or get_language()
    return t(text, lang=lang, **kwargs)