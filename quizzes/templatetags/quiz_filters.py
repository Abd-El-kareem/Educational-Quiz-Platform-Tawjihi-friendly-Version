import re
from urllib.parse import urlparse

import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

KHATT_HOST = "khatt.org"

ALLOWED_TAGS = ["img"]
ALLOWED_ATTRIBUTES = {"img": ["src", "width", "height", "alt", "class"]}

_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_SRC_RE = re.compile(r"""src\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.IGNORECASE)


def _img_src(tag):
    match = _SRC_RE.search(tag)
    if not match:
        return ""
    return match.group(1) or match.group(2) or match.group(3) or ""


def _is_khatt_img(tag):
    src = _img_src(tag)
    if not src:
        return False
    url = src if src.startswith(("http://", "https://", "//")) else f"https://{src}"
    try:
        return urlparse(url).hostname == KHATT_HOST
    except ValueError:
        return False


def _drop_foreign_imgs(text):
    return _IMG_RE.sub(lambda m: m.group(0) if _is_khatt_img(m.group(0)) else "", text)


@register.filter
def has_khatt_img(value):
    """True if the value contains at least one khatt.org ``<img>`` tag.

    Used by templates to decide whether stored content should be rendered as
    images (via ``rich``) regardless of the current UI language, so quizzes
    authored with the Arabic editor display correctly when viewed in English.
    """
    if value is None:
        return False
    for m in _IMG_RE.finditer(str(value)):
        if _is_khatt_img(m.group(0)):
            return True
    return False


@register.filter
def rich(value):
    """Render stored question/answer text as safe HTML.

    Only ``<img>`` tags whose ``src`` points at khatt.org are kept; everything
    else (including stray tags, event handlers, foreign image hosts) is stripped
    or escaped. Used for Arabic ``(khatt)`` math content authored via the symbol
    palette. Returns a ``SafeString``.
    """
    if value is None:
        return mark_safe("")
    html = _drop_foreign_imgs(str(value))
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=False,
    )
    return mark_safe(cleaned)