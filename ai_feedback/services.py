"""Ollama-powered question explanations.

Prompt building lives here (not in the view) and the raw markdown response is
sanitized before returning HTML to the client. Ollama is called through its
OpenAI-compatible API (``/v1/chat/completions``).
"""

import logging
import re

import bleach
import httpx
import markdown as md
from django.conf import settings

from core.khatt_latex import formula_marker, khatt_command_from_src

logger = logging.getLogger(__name__)

ALLOWED_TAGS = [
    "p", "br", "hr", "em", "strong", "code", "pre", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6", "a",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "target", "rel"]}


class AiFeedbackError(RuntimeError):
    pass


_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_IMG_SRC_RE = re.compile(r'src\s*=\s*(?:"([^"]*)"|\'([^\']*)\')', re.IGNORECASE)
_IMG_ALT_RE = re.compile(r'alt\s*=\s*(?:"([^"]*)"|\'([^\']*)\')', re.IGNORECASE)

# Kaggle/math handling: KaTeX auto-render needs delimited math. We pull every
# math span out of the markdown source (replacing it with a sentinel the markdown
# processor will not touch) so existing delimiters like ``\(...\)`` are preserved
# verbatim, and we wrap bare LaTeX like ``\frac{x + 1}{2}`` in ``\(...\)`` so the
# model never has to remember to. Spans are restored after markdown -> HTML.
_MATH_SENTINEL = "\x01MATH{}"

_PROTECTED_MATH_RE = re.compile(
    r"```.*?```"  # fenced code
    r"|\$\$(?:(?!\$\$)[\s\S])*?\$\$"  # $$ display $$
    r"|\$[^$\n]+\$"  # $ inline $
    r"|\\\([\s\S]*?\\\)"  # \( inline \)
    r"|\\\[[\s\S]*?\\\]"  # \[ display \]
    r"|`[^`]*`",  # `inline code`
)

_LATEX_COMMAND_RE = re.compile(r"\\([A-Za-z]+)")
_SENTENCE_BREAKS = set(".,;:!?")
_MATH_OPERATORS = set("=+<>/*-()@~|")
_AR_RANGE_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f]")
_PROSE_LATEX = frozenset({
    "textbf", "textit", "textsf", "texttt", "textcolor", "text",
    "emph", "mbox", "displaystyle", "mathrm",
})


def _is_arabic(ch):
    return bool(_AR_RANGE_RE.match(ch))


def _run_end(text, i):
    """Return the index just past a self-contained LaTeX run starting at ``i``.

    A run starts after a command name and extends through its brace groups,
    operator tokens, sub/superscripts and single-letter variables. It stops
    before real words (prose) or sentence punctuation so ``\frac{a}{b}`` in
    "Simplify \frac{a}{b} into lowest terms" wraps without eating the words.
    """
    n = len(text)
    depth = 0
    end = i
    while i < n:
        ch = text[i]
        if depth:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
            i += 1
            continue
        if ch == "{":
            depth = 1
            i += 1
            end = i
            continue
        if ch == "\\":
            cm = _LATEX_COMMAND_RE.match(text, i)
            if cm:
                i = cm.end()
                end = i
            else:
                i += 1
            continue
        if ch in "^_":
            i += 1
            end = i
            continue
        if ch == " ":
            i += 1
            continue
        if ch.isdigit() or ch in _MATH_OPERATORS:
            i += 1
            end = i
            continue
        if ch.isalpha():
            nxt = text[i + 1] if i + 1 < n else ""
            if (_is_arabic(ch) and nxt and _is_arabic(nxt)) or (
                not _is_arabic(ch) and nxt and nxt.isalpha()
            ):
                break
            i += 1
            end = i
            continue
        if ch in _SENTENCE_BREAKS:
            if ch == "." and i > 0 and text[i - 1].isdigit():
                i += 1
                end = i
                continue
            break
        break
    return end


def _wrap_bare_latex(text, spans):
    """Replace bare LaTeX runs with math sentinels; record ``\(run\)`` spans."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        m = _LATEX_COMMAND_RE.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        i = m.start()
        if m.group(1) in _PROSE_LATEX:
            out.append(text[i:m.end()])
            i = m.end()
            continue
        end = _run_end(text, m.end())
        run = text[i:end].strip()
        if not run:
            out.append(text[i:m.end()])
            i = m.end()
            continue
        spans.append(r"\(" + run + r"\)")
        out.append(_MATH_SENTINEL.format(len(spans) - 1))
        i = end
    return "".join(out)


def _protect_math(raw):
    spans = []
    out = []
    pos = 0
    for m in _PROTECTED_MATH_RE.finditer(raw):
        out.append(_wrap_bare_latex(raw[pos:m.start()], spans))
        spans.append(m.group(0))
        out.append(_MATH_SENTINEL.format(len(spans) - 1))
        pos = m.end()
    out.append(_wrap_bare_latex(raw[pos:], spans))
    return "".join(out), spans


def _restore_math(text, spans):
    for i, span in enumerate(spans):
        text = text.replace(_MATH_SENTINEL.format(i), span)
    return text


def _strip_math_images(text):
    """Replace embedded Khatt <img> tags with their LaTeX form.

    The maths command is recovered from the image's ``src`` (?c=) and expanded
    into LaTeX (``core.khatt_latex``) so the LLM understands the formula rather
    than guessing from the Arabic palette label. Falls back to the alt text when
    the command cannot be recovered, then to a bare ``[formula]``.
    """
    if not text:
        return text

    def _repl(match):
        tag = match.group(0)
        src_match = _IMG_SRC_RE.search(tag)
        src = src_match.group(1) or src_match.group(2) if src_match else ""
        command = khatt_command_from_src(src)
        if command:
            return formula_marker(command)
        alt_match = _IMG_ALT_RE.search(tag)
        if alt_match:
            alt = alt_match.group(1) or alt_match.group(2)
            return f"[formula: {alt}]" if alt else "[formula]"
        return "[formula]"

    return _IMG_TAG_RE.sub(_repl, text)


def build_prompt(question, selected_answer=None, lang="en"):
    lang_instruction = (
        "Respond in Arabic." if lang == "ar" else "Respond in English."
    )
    lines = [
        "You are a helpful tutor for an educational quiz.",
        "Explain the question below and why the correct answer is correct.",
        "Keep it concise (about 3-6 short sentences). Use markdown.",
        ("[formula: ...] tags contain the LaTeX form of an embedded math "
         "formula image used in the quiz; read them as the formula itself."),
        ("Wrap any math you write in \\( ... \\) (inline) or $$ ... $$ "
         "(display)."),
        lang_instruction,
        "",
        f"QUESTION: {_strip_math_images(question.text)}",
        "ANSWERS:",
    ]
    for answer in question.answers.all():
        marker = "(correct)" if answer.is_correct else ""
        lines.append(f"- {_strip_math_images(answer.text)} {marker}".rstrip())
    if selected_answer is not None:
        lines.append(f"\nThe user selected: {_strip_math_images(selected_answer.text)}")
    else:
        lines.append("\nThe user did not select an answer.")
    if lang == "ar":
        lines.append("\nRespond in Arabic.")
    return "\n".join(lines)


def _auth_headers():
    if settings.OLLAMA_API_KEY:
        return {"Authorization": f"Bearer {settings.OLLAMA_API_KEY}"}
    return {}


def _require_configured():
    if "ollama.com" in settings.OLLAMA_HOST and not settings.OLLAMA_API_KEY:
        raise AiFeedbackError(
            "Ollama Cloud API key is not configured (OLLAMA_API_KEY). "
            "Create one at https://ollama.com/settings/keys"
        )


def ask_for_explanation(question, selected_answer=None, lang="en"):
    """Call Ollama (Cloud or local) and return sanitized HTML."""
    _require_configured()
    url = f"{settings.OLLAMA_HOST.rstrip('/')}/v1/chat/completions"
    try:
        response = httpx.post(
            url,
            headers=_auth_headers(),
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You provide short, clear explanations in markdown. "
                            "Wrap any math in \\( ... \\) (inline) or $$ ... $$ (display)."
                        ),
                    },
                    {"role": "user", "content": build_prompt(question, selected_answer, lang)},
                ],
                "temperature": 0.3,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        raw_markdown = response.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning(
            "Ollama request failed for question %s (%s): %s", question.id, url, exc
        )
        raise AiFeedbackError("The AI explanation could not be generated right now.") from exc

    return markdown_to_html(raw_markdown)


def markdown_to_html(raw_markdown):
    safe, spans = _protect_math(raw_markdown or "")
    html = md.markdown(safe, extensions=["extra", "fenced_code"])
    html = _restore_math(html, spans)
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
