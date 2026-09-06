from types import SimpleNamespace
from unittest import mock
from urllib.parse import quote

import httpx
import pytest
from django.test import override_settings

from ai_feedback import services
from quizzes.tests.factories import make_quiz


@pytest.fixture
def question(db):
    quiz = make_quiz(
        question_specs=[
            ("What is 2+2?", 10, [("4", True), ("5", False)]),
        ]
    )
    return quiz.questions.get()


def fake_ollama(content):
    return SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": content}}]},
    )


def test_build_prompt_includes_content(question):
    prompt = services.build_prompt(question)
    assert "What is 2+2?" in prompt
    assert "- 4 (correct)" in prompt
    assert "did not select an answer" in prompt


def test_build_prompt_includes_selected_answer(question):
    selected = question.answers.get(is_correct=False)
    prompt = services.build_prompt(question, selected)
    assert "The user selected: 5" in prompt


def test_build_prompt_strips_khatt_images(question):
    question.text = (
        'ما قيمة <img src="https://khatt.org/api?c=%D8%B3" width="50" height="20" alt="كسر">؟'
    )
    prompt = services.build_prompt(question)
    assert '<img' not in prompt
    assert 'width="50"' not in prompt
    assert "[formula: x]" in prompt
    assert "ما قيمة" in prompt


def test_build_prompt_latex_for_khatt_formula_in_english(question):
    command = "/على{س + 1}{2}"
    src = "https://khatt.org/api?c=" + quote(command, safe="")
    question.text = f"احسب <img src=\"{src}\" alt=\"كسر\"> الآن"
    prompt = services.build_prompt(question)

    assert r"[formula: \frac{x + 1}{2}]" in prompt
    assert "alt=\"كسر\"" not in prompt


def test_build_prompt_latex_for_khatt_formula_in_arabic(question):
    command = "/نها{س}{3}"
    src = "https://khatt.org/api?c=" + quote(command, safe="")
    question.text = f"أوجد <img src=\"{src}\" alt=\"نهاية\">"
    prompt = services.build_prompt(question, lang="ar")

    assert r"[formula: \lim_{3}{x}]" in prompt
    assert prompt.rstrip().endswith("Respond in Arabic.")


def test_build_prompt_appends_raw_command_for_unknown_tokens(question):
    command = "/مجموع{س}"
    src = "https://khatt.org/api?c=" + quote(command, safe="")
    question.text = f"<img src=\"{src}\" alt=\"كسر\">"
    prompt = services.build_prompt(question)

    assert "[formula: مجموع x; raw: /مجموع{س}]" in prompt


def test_build_prompt_falls_back_to_alt_without_command(question):
    question.text = (
        'ما قيمة <img src="https://evil.example/x.png" width="50" alt="كسر">؟'
    )
    prompt = services.build_prompt(question)
    assert "[formula: كسر]" in prompt


def test_build_prompt_latex_for_answer_and_selection(question):
    command = "/جذر{4}"
    src = "https://khatt.org/api?c=" + quote(command, safe="")
    correct = question.answers.get(is_correct=True)
    correct.text = f"<img src=\"{src}\" alt=\"جذر\">"
    correct.save()
    question.answers.get(is_correct=False).text = "other"
    prompt = services.build_prompt(question, correct)

    assert r"[formula: \sqrt{4}] (correct)" in prompt
    assert r"The user selected: [formula: \sqrt{4}]" in prompt


def test_build_prompt_tells_llm_how_to_read_formula_tags(question):
    prompt = services.build_prompt(question)
    assert "LaTeX" in prompt


def test_build_prompt_tells_llm_to_delimit_math(question):
    prompt = services.build_prompt(question)
    assert r"\( ... \)" in prompt


def test_markdown_to_html_wraps_bare_latex():
    html = services.markdown_to_html(r"The value is \frac{x + 1}{2}.")
    assert r"\(\frac{x + 1}{2}\)" in html


def test_markdown_to_html_wraps_bare_latex_with_subscripts():
    html = services.markdown_to_html(r"Total is \sum_{i=1}^{n} i.")
    assert r"\(\sum_{i=1}^{n} i\)" in html


def test_markdown_to_html_stops_latex_run_at_prose():
    html = services.markdown_to_html(r"Simplify \frac{a}{b} into lowest terms.")
    assert r"\(\frac{a}{b}\)" in html
    assert "into lowest terms" in html


def test_markdown_to_html_stops_latex_run_at_arabic_prose():
    html = services.markdown_to_html(r"القيمة هي \frac{a}{b} والنتيجة سهلة.")
    assert r"\(\frac{a}{b}\)" in html
    assert "القيمة هي" in html


def test_markdown_to_html_preserves_existing_math_delimiters():
    html = services.markdown_to_html(r"Already \(x^2\) and $\frac{a}{b}$.")
    assert r"\(x^2\)" in html
    assert r"$\frac{a}{b}$" in html
    assert r"\((x^2)\)" not in html


def test_markdown_to_html_preserves_display_math_and_code():
    html = services.markdown_to_html(
        r"$$\frac{1}{2}$$ and `code \frac{raw}{kept}`"
    )
    assert r"$$\frac{1}{2}$$" in html
    assert r"`code \frac{raw}{kept}`" in html


def test_markdown_to_html_still_renders_markdown_emphasis():
    html = services.markdown_to_html(r"**Bold** and \frac{1}{2} together.")
    assert "<strong>Bold</strong>" in html
    assert r"\(\frac{1}{2}\)" in html


@override_settings(OLLAMA_API_KEY="test-key")
@mock.patch("ai_feedback.services.httpx.post")
def test_ask_for_explanation_renders_sanitized_html(mock_post, question):
    mock_post.return_value = fake_ollama("**Great!** It is 4.")
    html = services.ask_for_explanation(question)

    assert "<strong>Great!</strong>" in html
    assert "It is 4." in html
    assert mock_post.call_args.kwargs["json"]["model"] == "gpt-oss:120b"
    assert mock_post.call_args.kwargs["timeout"] == 60.0
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


@override_settings(OLLAMA_API_KEY="test-key")
@mock.patch("ai_feedback.services.httpx.post")
def test_ask_for_explanation_strips_dangerous_html(mock_post, question):
    content = "Answer: 4\n\n<script>alert('x')</script>\n\n<a href='javascript:evil'>link</a>"
    mock_post.return_value = fake_ollama(content)
    html = services.ask_for_explanation(question)

    assert "<script" not in html
    assert "javascript:" not in html
    assert "Answer: 4" in html


def test_cloud_requires_api_key(question):
    with override_settings(OLLAMA_API_KEY="", OLLAMA_HOST="https://ollama.com"):
        with pytest.raises(services.AiFeedbackError, match="OLLAMA_API_KEY"):
            services.ask_for_explanation(question)


@mock.patch("ai_feedback.services.httpx.post")
def test_local_host_works_without_key(mock_post, question):
    with override_settings(OLLAMA_API_KEY="", OLLAMA_HOST="http://localhost:11434"):
        mock_post.return_value = fake_ollama("local ok")
        html = services.ask_for_explanation(question)
    assert "local ok" in html
    assert mock_post.call_args.kwargs["headers"] == {}


@override_settings(OLLAMA_API_KEY="sekret")
@mock.patch("ai_feedback.services.httpx.post")
def test_sends_auth_header_when_key_configured(mock_post, question):
    mock_post.return_value = fake_ollama("ok")
    services.ask_for_explanation(question)
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer sekret"


@mock.patch("ai_feedback.services.httpx.post")
def test_connection_error_raises_friendly_error(mock_post, question):
    mock_post.side_effect = httpx.ConnectError("refused")
    with pytest.raises(services.AiFeedbackError):
        services.ask_for_explanation(question)


@mock.patch("ai_feedback.services.httpx.post")
def test_http_error_raises_friendly_error(mock_post, question):
    def fail():
        raise httpx.HTTPStatusError("400", request=mock.ANY, response=mock.ANY)

    mock_post.return_value = SimpleNamespace(raise_for_status=fail)
    with pytest.raises(services.AiFeedbackError):
        services.ask_for_explanation(question)
