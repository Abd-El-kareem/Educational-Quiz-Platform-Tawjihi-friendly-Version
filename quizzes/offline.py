"""Offline quiz export: render a quiz as a self-contained, workable HTML file.

The generated file bundles every asset it needs to run with no network:
- the live quiz/review styling (``offline_quiz.css``) and taking logic
  (``offline_quiz.js``),
- KaTeX (JS/CSS/fonts) when the quiz contains LaTeX math questions,
- khatt formula images and uploaded question images as ``data:`` URIs.

Scoring and the post-submit review run entirely in the browser from the
embedded ``data-correct`` flags; nothing in the file talks to a server.
"""

import base64
import json
import logging
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import escape, mark_safe

from core.translations import t
from quizzes import selectors as quiz_selectors
from quizzes.templatetags import quiz_filters

logger = logging.getLogger(__name__)

KATEX_VERSION = "0.16.11"
KATEX_BASE = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist"

_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_SRC_RE = re.compile(
    r"""src\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.IGNORECASE
)
_FONT_REF_RE = re.compile(
    r'(?P<comma>,\s*)?url\(\s*(?P<quote>["\']?)(?P<file>fonts/[^)()\'"]+)(?P=quote)\s*\)'
)

# Strings used by the offline file (server-rendered labels + JS blink).
_STRING_KEYS = (
    "Quiz",
    "Category",
    "Question",
    "pts",
    "points total",
    "Time Remaining",
    "Submit quiz",
    "Previous",
    "Next",
    "saved",
    "Question image",
    "Offline quiz",
    "Offline practice file — answers are saved in this browser only, not to the server.",
    "Please answer all questions before submitting:",
    "Your answer",
    "Correct answer",
    "Not answered",
    "Your score: {earned} / {total}",
    "Correct answers: {correct} of {total}",
    "Retake quiz",
    "Time's up! Your answers were submitted.",
)

# Template-friendly (snake_case) names for the labels used via dot lookup.
_SLUG_KEYS = {
    "quiz": "Quiz",
    "category": "Category",
    "question": "Question",
    "s": "s",
    "pts": "pts",
    "points_total": "points total",
    "time_remaining": "Time Remaining",
    "submit_quiz": "Submit quiz",
    "previous": "Previous",
    "next": "Next",
    "saved": "saved",
    "question_image": "Question image",
    "offline_badge": "Offline quiz",
    "offline_note": "Offline practice file — answers are saved in this browser only, not to the server.",
    "unanswered_alert": "Please answer all questions before submitting:",
    "retake": "Retake quiz",
}

_fetch_cache = {}


def _fetch_bytes(url, timeout=10.0):
    """Download a remote asset. Returns bytes, or None on any failure.

    Cached per URL so repeated khatt/KaTeX fetches hit the network once.
    Tests monkeypatch this function directly (bypassing the cache).
    """
    if url in _fetch_cache:
        return _fetch_cache[url]
    data = None
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        data = response.content
    except Exception as exc:  # noqa: BLE001 - any network failure degrades gracefully
        logger.warning("Offline export fetch failed for %s: %s", url, exc)
    _fetch_cache[url] = data
    return data


def _img_src(tag):
    match = _SRC_RE.search(tag)
    if not match:
        return ""
    return match.group(1) or match.group(2) or match.group(3) or ""


def _embed_khatt(html):
    """Replace ``khatt.org`` image srcs with base64 data URIs (offline-safe)."""

    def _repl(match):
        tag = match.group(0)
        original = _img_src(tag)
        if not original:
            return tag
        candidate = original
        if candidate.startswith("//"):
            candidate = "https:" + candidate
        elif not candidate.startswith(("http://", "https://")):
            candidate = "https://" + candidate
        try:
            host = urlsplit(candidate).netloc
        except ValueError:
            return tag
        if host != "khatt.org":
            return tag
        data = _fetch_bytes(candidate)
        if not data:
            return tag
        encoded = base64.b64encode(data).decode("ascii")
        return tag.replace(original, f"data:image/png;base64,{encoded}", 1)

    return _IMG_RE.sub(_repl, html)


def _image_data_uri(image_field):
    """Base64 ``data:`` URI for an uploaded question image, or "" when absent."""
    if not image_field:
        return ""
    try:
        path = image_field.path
        name = image_field.name
    except Exception:  # noqa: BLE001 - missing/invalid file degrades gracefully
        return ""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return ""
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _embed_katex_fonts(css):
    """Inline the woff2 fonts referenced by KaTeX CSS; drop woff/ttf fallbacks."""

    def _repl(match):
        name = match.group("file")
        if not name.endswith(".woff2"):
            return ""
        data = _fetch_bytes(f"{KATEX_BASE}/{name}")
        if not data:
            return match.group(0)
        encoded = base64.b64encode(data).decode("ascii")
        return f'url("data:font/woff2;base64,{encoded}")'

    return _FONT_REF_RE.sub(_repl, css)


def _katex_assets():
    """Return {css, js, autorender_js} for KaTeX, or None when unavailable."""
    js = _fetch_bytes(f"{KATEX_BASE}/katex.min.js")
    css = _fetch_bytes(f"{KATEX_BASE}/katex.min.css")
    autorender = _fetch_bytes(f"{KATEX_BASE}/contrib/auto-render.min.js")
    if not (js and css and autorender):
        return None
    return {
        "js": js.decode("utf-8", "replace"),
        "css": _embed_katex_fonts(css.decode("utf-8", "replace")),
        "autorender_js": autorender.decode("utf-8", "replace"),
    }


def _read_static(relative):
    try:
        return (Path(settings.BASE_DIR) / "static" / relative).read_text(
            encoding="utf-8"
        )
    except OSError:
        return ""


def _question_html(value, lang):
    """HTML for question/answer text: khatt images embedded, otherwise escaped."""
    if quiz_filters.has_khatt_img(value):
        return mark_safe(_embed_khatt(str(quiz_filters.rich(value))))
    return mark_safe(escape(str(value)))


def render_offline_quiz(quiz, lang="en"):
    """Return a full standalone HTML string for ``quiz`` in ``lang``.

    The file is fully offline: KaTeX + fonts, khatt images, and uploaded
    question images are all inlined as ``data:`` URIs.
    """
    direction = "rtl" if lang == "ar" else "ltr"
    strings = {k: t(k, lang) for k in _STRING_KEYS}
    strings.update({slug: t(key, lang) for slug, key in _SLUG_KEYS.items()})

    questions = []
    for index, question in enumerate(quiz.questions.all(), start=1):
        is_khatt = quiz_filters.has_khatt_img(question.text)
        questions.append(
            {
                "pk": question.id,
                "index": index,
                "points": question.points,
                "math_enabled": question.math_enabled,
                "is_khatt": is_khatt,
                "text_html": _question_html(question.text, lang),
                "image": _image_data_uri(question.image),
                "answers": [
                    {
                        "id": answer.id,
                        "html": _question_html(answer.text, lang),
                        "correct": answer.is_correct,
                    }
                    for answer in question.answers.all()
                ],
            }
        )

    has_math = any(q.math_enabled for q in quiz.questions.all())
    has_katex = has_math and lang != "ar"

    katex = _katex_assets() if has_katex else None
    context = {
        "lang": lang,
        "dir": direction,
        "quiz_title": quiz.title,
        "category_name": quiz.category.name,
        "question_count": len(questions),
        "total_points": quiz_selectors.quiz_total_points(quiz),
        "time_limit_minutes": quiz.time_limit_minutes,
        "questions": questions,
        "strings": strings,
        "i18n_json": json.dumps(strings, ensure_ascii=False),
        "has_katex": has_katex,
        "katex_css": (katex or {}).get("css", ""),
        "katex_js": (katex or {}).get("js", ""),
        "katex_autorender_js": (katex or {}).get("autorender_js", ""),
        "offline_css": _read_static("css/offline_quiz.css"),
        "offline_js": _read_static("js/offline_quiz.js"),
    }
    return render_to_string("quizzes/offline_quiz.html", context)