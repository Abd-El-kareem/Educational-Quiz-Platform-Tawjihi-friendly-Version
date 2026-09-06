"""KhattSeen command -> LaTeX.

Khatt formula images are stored as ``<img src="https://khatt.org/api?c=...">``
where ``?c=`` is the percent-encoded KhattSeen command that rendered the image.
This module turns such commands into an equivalent LaTeX snippet so an LLM can
reason about the math even though it never sees the image.

The grammar mirrors the official reference at https://khatt.org/documentation
and the authoring palette in static/js/khatt_helper.js. Single-letter Arabic
variables (س، ص، ع، ...) are transliterated to Latin letters so the LaTeX reads
naturally; multi-letter Arabic text is left untouched. Commands the parser does
not recognize are emitted verbatim and reported as unknown so the caller can
append the untouched command as a fallback for the LLM.
"""

import re
from urllib.parse import unquote, urlsplit

_SPECIAL = set('/#"{}()[]^"')

_WS = re.compile(r"\s+")
_PLACEHOLDER = re.compile(r"\{(\d+)\}")
_AR_LETTER = re.compile(r"[سصضقفغعهخحجدطكمنتالبيسرأإآةوؤىيئ]")


def _fmt(pattern, args):
    def _repl(m):
        idx = int(m.group(1))
        return args[idx] if idx < len(args) else ""

    return _PLACEHOLDER.sub(_repl, pattern)


def _join(parts):
    # Join tokens with single spaces; LaTeX ignores whitespace inside math.
    return _WS.sub(" ", " ".join(p for p in parts if p)).strip()


def _skip_spaces(text, i):
    crossed_newline = False
    j = i
    while j < len(text) and text[j] in " \t\r\n":
        if text[j] in "\r\n":
            crossed_newline = True
        j += 1
    return j, crossed_newline


def _read_word(text, i):
    j = i
    while j < len(text):
        ch = text[j]
        if ch == "." or ch == "_" or ch.isalnum():
            j += 1
        else:
            break
    return text[i:j], j


def _read_group(text, i):
    """Read a brace group starting at ``{``; return (content, next_index)."""
    depth = 0
    quoted = False
    j = i
    while j < len(text):
        ch = text[j]
        if quoted:
            if ch == '"':
                if j + 1 < len(text) and text[j + 1] == '"':
                    j += 2
                    continue
                quoted = False
            j += 1
            continue
        if ch == '"':
            quoted = True
            j += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1 : j], j + 1
        j += 1
    return text[i + 1 :], len(text)


def _read_args(text, i):
    """Read consecutive brace groups; return (contents, row_breaks, next_index).

    ``row_breaks[i]`` (for i > 0) is True when a new line separated argument
    i-1 from argument i, which matters for /مصفوفة. The newline right after
    the command name is not a row break.
    """
    args = []
    row_breaks = []
    j = i
    first = True
    while True:
        k, crossed = _skip_spaces(text, j)
        if k >= len(text) or text[k] != "{":
            break
        content, k = _read_group(text, k)
        args.append(content)
        row_breaks.append(crossed and not first)
        first = False
        j = k
    return args, row_breaks, j


def _read_quoted(text, i):
    out = []
    j = i + 1
    while j < len(text):
        ch = text[j]
        if ch == '"':
            if j + 1 < len(text) and text[j + 1] == '"':
                out.append('"')
                j += 2
                continue
            return "".join(out), j + 1
        out.append(ch)
        j += 1
    return "".join(out), j


def _read_plain(text, i):
    j = i
    while j < len(text) and text[j] not in _SPECIAL and text[j] not in " \t\r\n":
        j += 1
    return text[i:j], j


def _read_option(text, i):
    """Skip a ``#...`` option command plus any brace arguments."""
    j = i + 1
    while j < len(text) and (text[j].isalnum() or text[j] in "._"):
        j += 1
    while True:
        k, _ = _skip_spaces(text, j)
        if k < len(text) and text[k] == "{":
            _, k = _read_group(text, k)
            j = k
        else:
            return k


def _handle_power(text, i, ctx):
    """If ``text[i]`` starts a caret, return (exp_string, next_index).

    The caret binds the *previous* atom as its base, so the caller composes the
    "base^{exp}" after it already emitted the base.
    """
    k, _ = _skip_spaces(text, i)
    if k >= len(text) or text[k] != "^":
        return None, i
    k += 1
    k, _ = _skip_spaces(text, k)
    if k < len(text) and text[k] == "{":
        content, k = _read_group(text, k)
        return _join(_parse(content, ctx)), k
    return None, k


def _transliterate(run):
    """Map single-letter Arabic variables (س، ص، ...) to Latin.

    A run holding a single Arabic letter (optionally with digits, e.g. ``2أ``)
    is a variable and gets transliterated. Runs containing two or more Arabic
    letters are prose (e.g. an Arabic word) and are left untouched.
    """
    letters = _AR_LETTER.findall(run)
    if len(letters) >= 2:
        return run
    return "".join(_AR_MAP.get(ch, ch) for ch in run)


# Single-letter Arabic variables -> Latin. س=ن ص are the classic (س، ص)
# coordinate pair; the rest follow the common Arabic math set أ ب ج د = a b c d.
_AR_MAP = {
    "س": "x",
    "ص": "y",
    "أ": "a",
    "ب": "b",
    "ج": "c",
    "د": "d",
    "ع": "c",
    "م": "m",
    "ن": "n",
    "ك": "k",
    "ل": "l",
}


def _parse(text, ctx):
    parts = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "#":
            i = _read_option(text, i)
        elif ch == "/":
            i = _parse_slash(text, i, parts, ctx)
        elif ch == "{":
            content, j = _read_group(text, i)
            sub = _join(_parse(content, ctx))
            exp, j2 = _handle_power(text, j, ctx)
            if exp is not None:
                parts.extend(_power_parts(sub, exp))
                i = j2
            else:
                parts.append(sub)
                i = j
        elif ch in "([":
            closer = ")" if ch == "(" else "]"
            content, j = _read_delimited(text, i, closer)
            sub = _join(_parse(content, ctx))
            exp, j2 = _handle_power(text, j, ctx)
            parts.append("\\left" + ch)
            parts.append(sub)
            parts.append("\\right" + closer)
            if exp is not None:
                parts.extend(_power_parts("", exp))
                i = j2
            else:
                i = j
        elif ch == '"':
            content, j = _read_quoted(text, i)
            parts.append(content)
            i = j
        elif ch in ")}]":
            i += 1
        elif ch == "^":
            i += 1
        elif ch in " \t\r\n":
            i += 1
        else:
            run, j = _read_plain(text, i)
            if run:
                parts.append(_transliterate(run))
            i = j
    return parts


def _read_delimited(text, i, closer):
    depth = 0
    quoted = False
    j = i
    while j < len(text):
        ch = text[j]
        if quoted:
            if ch == '"':
                if j + 1 < len(text) and text[j + 1] == '"':
                    j += 2
                    continue
                quoted = False
            j += 1
            continue
        if ch == '"':
            quoted = True
            j += 1
            continue
        if ch in "([{" and ch != closer:
            depth += 1
        elif ch == closer:
            if depth == 0:
                return text[i + 1 : j], j + 1
            depth -= 1
        elif ch == "}" and closer != "}":
            depth -= 1
        j += 1
    return text[i + 1 :], len(text)


def _parse_slash(text, i, parts, ctx):
    n = len(text)
    j = i + 1
    if j < n and text[j] == "/":
        parts.append("/")
        return j + 1
    word, j = _read_word(text, j)
    if not word:
        parts.append("/")
        return j
    if word.startswith("."):
        parts.append(_symbol(word[1:], ctx))
        return j
    if word.isdigit():
        try:
            parts.append(chr(int(word, 16)))
        except ValueError:
            parts.append(word)
        return j
    if word in _STRUCTURE_WORDS:
        args, row_breaks, j = _read_args(text, j)
        parts.append(_structure(word, args, row_breaks, ctx))
        return j
    if word in _IGNORED:
        _, _, j = _read_args(text, j)
        return j
    args, _, j = _read_args(text, j)
    args_v = [_join(_parse(a, ctx)) for a in args]
    parts.append(" ".join([word] + args_v))
    ctx["unknown"] = True
    return j


def _symbol(word, ctx):
    latex = SYMBOLS.get(word)
    if latex is not None:
        return latex
    ctx["unknown"] = True
    return word


def _power_parts(base, exp):
    return [f"{{{base}}}", "^", f"{{{exp}}}"]


def _fence(token):
    if token == "{":
        return "\\{"
    if token == "}":
        return "\\}"
    return token


def _structure(word, args, row_breaks, ctx):
    args_v = [_join(_parse(a, ctx)) for a in args]
    if word == "جذر":
        if len(args_v) <= 1:
            return f"\\sqrt{{{args_v[0] if args_v else ''}}}"
        return f"\\sqrt[{args_v[0]}]{{{args_v[1] if len(args_v) > 1 else ''}}}"
    if word == "مصفوفة":
        rows = []
        if args_v:
            current = [args_v[0]]
            for idx in range(1, len(args_v)):
                if row_breaks[idx]:
                    rows.append(" & ".join(current))
                    current = [args_v[idx]]
                else:
                    current.append(args_v[idx])
            rows.append(" & ".join(current))
        return "\\begin{matrix}" + " \\\\ ".join(rows) + "\\end{matrix}"
    if word == "عمود":
        cells = [c for c in args_v if c]
        return "\\begin{array}{c} " + " \\\\ ".join(cells) + " \\end{array}"
    if word in ("يلف", "يحتوي"):
        f0 = _fence(args_v[0] if len(args_v) > 0 else "")
        f2 = _fence(args_v[2] if len(args_v) > 2 else "")
        content = args_v[1] if len(args_v) > 1 else ""
        return f"\\left{f0} {content} \\right{f2}"
    if word == "مسافة":
        return "\\;"
    return _fmt(_LATEX[word], args_v)


# Function commands: LaTeX built from ``{0}``..``{n}`` args.
_LATEX = {
    "على": r"\frac{{0}}{{1}}",
    "مج": r"\sum_{{0}}^{{1}}",
    "تكا": r"\int_{{0}}^{{1}}",
    "نها": r"\lim_{{1}}{{0}}",
    "قوس": r"\left({0}\right)",
    "فوق": r"\overset{{1}}{{0}}",
    "تحت": r"\underset{{1}}{{0}}",
    "فو.تح": r"\overset{{1}}{{\underset{{2}}{{0}}}}",
    "م.فوق": r"\overset{{1}}{{0}}",
    "م.تحت": r"\underset{{1}}{{0}}",
    "م.فو.تح": r"\overset{{1}}{{\underset{{2}}{{0}}}}",
    "شخط": r"\cancel{{0}}",
    "عكس": r"{0}",
    "مضر": r"{0}",
    "لو.خل": r"{1}",
}

_STRUCTURE_WORDS = set(_LATEX) | {"جذر", "مصفوفة", "عمود"}
_IGNORED = {"سطر", "فراغ"}  # visual layout commands that contribute no LaTeX

# Literal symbols: LaTeX commands.
SYMBOLS = {
    "لا.نهاية": r"\infty",
    "يوجد": r"\exists",
    "باي": r"\pi",
    "خالية": r"\emptyset",
    "فرق": r"\smallsetminus",
    "لكل": r"\forall",
    "مج.غرب": r"\sum",
    "تكا": r"\int",
    "ضرب": r"\times",
    "قسمة": r"\div",
    "زائد.ناقص": r"\pm",
    "ناقص.زائد": r"\mp",
    "تقاطع": r"\cap",
    "اتحاد": r"\cup",
    "و": r"\land",
    "أو": r"\lor",
    "زائد.مدورة": r"\oplus",
    "ناقص.مدورة": r"\ominus",
    "ضرب.مدورة": r"\otimes",
    "شرطة.قسمة.مدورة": r"\oslash",
    "ناقص.مجموعة": r"\setminus",
    "عامل.الدائرة": r"\circ",
    "أكبر.يساوي": r"\geq",
    "أصغر.يساوي": r"\leq",
    "أكبر.بكثير": r"\gg",
    "أصغر.بكثير": r"\ll",
    "مطابق": r"\equiv",
    "جزئي.فعلي": r"\subset",
    "جزئي.يساوي": r"\subseteq",
    "متضمن.فعلي": r"\supset",
    "متضمن.يساوي": r"\supseteq",
    "ينتمي": r"\in",
    "يحتوي": r"\ni",
    "يساوي.تقريبا": r"\approx",
    "لا.يساوي": r"\neq",
    "ليس.أكبر": r"\not>",
    "ليس.أصغر": r"\not<",
    "ليس.أكبر.ولا.يساوي": r"\not\geq",
    "ليس.أصغر.ولا.يساوي": r"\not\leq",
    "غير.مطابق": r"\not\equiv",
    "ليس.جزئي.فعلي": r"\not\subset",
    "ليس.جزئي.ولا.يساوي": r"\not\subseteq",
    "ليس.متضمن": r"\not\supset",
    "ليس.متضمن.ولا.يساوي": r"\not\supseteq",
    "لا.ينتمي": r"\notin",
    "لا.يحتوي": r"\not\ni",
    "لا.يساوي.تقريبا": r"\not\approx",
    "سهم.يمين": r"\rightarrow",
    "سهم.يمين.مزدوج": r"\Rightarrow",
    "سهم.يسار": r"\leftarrow",
    "سهم.يسار.مزدوج": r"\Leftarrow",
    "سهم.ثنائي": r"\leftrightarrow",
    "سهم.ثنائي.مزدوج": r"\Leftrightarrow",
    "فاتحة.قاع": r"\lfloor",
    "فاتحة.سقف": r"\lceil",
    "فاتحة.معقوف.أبيض": r"\llbracket",
    "فاتحة.زاوية.مزدوجة": r"\langle",
    "غالقة.قاع": r"\rfloor",
    "غالقة.سقف": r"\rceil",
    "غالقة.معقوف.أبيض": r"\rrbracket",
    "غالقة.زاوية.مزدوجة": r"\rangle",
    "بما.أن": r"\because",
    "إذن": r"\therefore",
    "نقاط.حذف.عمودية": r"\vdots",
    "نقاط.حذف.أفقية": r"\ldots",
    "نقاط.حذف.أعلى.اليسار": r"\iddots",
    "نقاط.حذف.أدنى.اليسار": r"\ddots",
}


def khatt_command_from_src(src):
    """Extract and percent-decode the ``?c=`` khatt command from an image src.

    Returns None when the src is not a khatt.org image URL. ``+`` is preserved
    (parse_qs would turn it into a space, corrupting formulas).
    """
    if not src:
        return None
    try:
        parts = urlsplit(src)
    except ValueError:
        return None
    if parts.netloc != "khatt.org":
        return None
    for param in parts.query.split("&"):
        if param.startswith("c="):
            return unquote(param[2:])
    return None


def to_latex(command):
    """Return (latex, has_unknown_tokens) for a khatt command."""
    if not command:
        return "", False
    ctx = {"unknown": False}
    parts = _parse(command.strip(), ctx)
    return _join(parts), ctx["unknown"]


def formula_marker(command):
    """Return a ``[formula: ...]`` prompt placeholder for a khatt command.

    When the command contains tokens we could not translate, the untouched
    command is appended so the LLM can still reason about it.
    """
    text, unknown = to_latex(command)
    if not text:
        return "[formula]"
    if unknown:
        return f"[formula: {text}; raw: {command}]"
    return f"[formula: {text}]"