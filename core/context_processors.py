import json
from django.conf import settings
from django.utils.translation import get_language
from core.translations import AR, LANGUAGES, get_translations_json

def language_context(request):
    """Expose language state and JS translation blob to templates."""
    lang = get_language()
    return {
        "LANGUAGE_CODE": lang,
        "LANGUAGES": LANGUAGES,
        "RTL": lang == "ar",
        "dir": "rtl" if lang == "ar" else "ltr",
        "math_engine": "khatt" if lang == "ar" else "katex",
        "QUIZ_L10N_JSON": get_translations_json(lang),
    }
