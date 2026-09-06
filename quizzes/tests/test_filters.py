import pytest
from django.utils.safestring import SafeString

from quizzes.templatetags.quiz_filters import has_khatt_img, rich


def test_rich_returns_safe_string():
    assert isinstance(rich("نص"), SafeString)


def test_rich_keeps_khatt_img_with_dimensions():
    html = '<img src="https://khatt.org/api?c=%D8%B3" width="80" height="30" alt="س">'
    out = rich(html)
    assert "https://khatt.org/api?c=%D8%B3" in out
    assert 'width="80"' in out
    assert 'height="30"' in out
    assert 'alt="س"' in out


def test_rich_strips_script_and_event_handlers():
    html = (
        '<script>alert(1)</script>'
        '<img src="https://khatt.org/api?c=A" onerror="alert(1)">'
        "<b>بدن</b>"
    )
    out = rich(html)
    assert "<script" not in out
    assert "</script" not in out
    assert "onerror" not in out.lower()
    assert "<b>" not in out


def test_rich_drops_foreign_and_relative_imgs():
    html = '<img src="https://evil.com/x.png"><img src="/local.png">'
    out = rich(html)
    assert "evil.com" not in out
    assert "local.png" not in out
    assert "<img" not in out


def test_rich_protocol_relative_khatt_img_allowed():
    html = '<img src="//khatt.org/api?c=%D8%B3">'
    out = rich(html)
    assert "khatt.org" in out


def test_rich_none_is_blank():
    assert rich(None) == ""


def test_has_khatt_img_true_when_khatt_img_present():
    html = (
        "حل: <img src=\"https://khatt.org/api?c=%D8%B3\"> ثم <img src=\"//khatt.org/api?c=2\">"
        "<b>beside</b>"
    )
    assert has_khatt_img(html) is True


def test_has_khatt_img_false_for_plain_text_and_foreign_imgs():
    assert has_khatt_img("plain \\frac{1}{2}") is False
    assert has_khatt_img('<img src="https://evil.com/x.png">') is False
    assert has_khatt_img("<script>alert(1)</script>") is False


def test_has_khatt_img_none_is_false():
    assert has_khatt_img(None) is False