from types import SimpleNamespace
from unittest import mock
from urllib.parse import quote

import httpx
import pytest
from django.test import override_settings
from django.urls import reverse

from quizzes.tests.factories import make_quiz


@pytest.fixture
def quiz(db):
    return make_quiz(question_specs=[("Q", 10, [("A", True), ("B", False)])])


@pytest.fixture
def question(quiz):
    return quiz.questions.get()


def fake_ollama(content):
    return SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": content}}]},
    )


def test_explain_endpoint_returns_html(client, question):
    with mock.patch("ai_feedback.services.httpx.post") as mock_post:
        mock_post.return_value = fake_ollama("**Yes.**")
        with override_settings(OLLAMA_API_KEY="test-key"):
            response = client.post(reverse("ai_feedback:ai_explain", args=[question.id]))

    assert response.status_code == 200
    assert "<strong>Yes.</strong>" in response.data["html"]


def test_explain_endpoint_503_on_ollama_error(client, question):
    with mock.patch("ai_feedback.services.httpx.post") as mock_post:
        mock_post.side_effect = httpx.ConnectError("refused")
        with override_settings(OLLAMA_API_KEY="test-key"):
            response = client.post(reverse("ai_feedback:ai_explain", args=[question.id]))

    assert response.status_code == 503


def test_explain_endpoint_503_without_key(client, question):
    with override_settings(OLLAMA_API_KEY="", OLLAMA_HOST="https://ollama.com"):
        response = client.post(reverse("ai_feedback:ai_explain", args=[question.id]))

    assert response.status_code == 503


def test_explain_endpoint_404(client, db):
    with mock.patch("ai_feedback.services.httpx.post") as mock_post:
        with override_settings(OLLAMA_API_KEY="test-key"):
            response = client.post(reverse("ai_feedback:ai_explain", args=[999999]))

    assert response.status_code == 404
    mock_post.assert_not_called()


def test_explain_latex_for_khatt_formula_in_prompt(client, quiz, question):
    command = "/على{س + 1}{2}"
    src = "https://khatt.org/api?c=" + quote(command, safe="")
    question.text = f'احسب <img src="{src}" alt="كسر"> الآن'
    question.save()

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["prompt"] = json["messages"][1]["content"]
        return fake_ollama("**OK.**")

    with mock.patch("ai_feedback.services.httpx.post") as mock_post:
        mock_post.side_effect = fake_post
        with override_settings(OLLAMA_API_KEY="test-key"):
            response = client.post(reverse("ai_feedback:ai_explain", args=[question.id]))

    assert response.status_code == 200
    assert r"[formula: \frac{x + 1}{2}]" in captured["prompt"]
    assert "LaTeX" in captured["prompt"]
    assert "<img" not in captured["prompt"]


def _submit_as(user, client, quiz, question):
    from django.urls import reverse as url_reverse

    client.force_login(user)
    wrong = question.answers.get(is_correct=False)
    client.post(
        url_reverse("scoring_api:save_answer", args=[quiz.id]),
        {"question_id": question.id, "answer_id": wrong.id},
        content_type="application/json",
    )
    client.post(url_reverse("scoring_api:submit_quiz", args=[quiz.id]))


def test_explain_uses_attempt_answer_when_score_id_given(client, quiz, question):
    from quizzes.tests.factories import UserFactory
    from scoring.models import Score

    user = UserFactory()
    _submit_as(user, client, quiz, question)
    score = Score.objects.get(user=user, quiz=quiz)

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["prompt"] = json["messages"][1]["content"]
        return fake_ollama("**OK.**")

    with mock.patch("ai_feedback.services.httpx.post") as mock_post:
        mock_post.side_effect = fake_post
        with override_settings(OLLAMA_API_KEY="test-key"):
            response = client.post(
                reverse("ai_feedback:ai_explain", args=[question.id]),
                data={"score_id": score.id},
                content_type="application/json",
            )

    assert response.status_code == 200
    assert "The user selected: B" in captured["prompt"]


def test_explain_with_foreign_score_id_returns_404(client, quiz, question):
    from quizzes.tests.factories import UserFactory
    from scoring.models import Score

    owner = UserFactory()
    _submit_as(owner, client, quiz, question)
    score = Score.objects.get(user=owner, quiz=quiz)

    other = UserFactory()
    client.force_login(other)
    response = client.post(
        reverse("ai_feedback:ai_explain", args=[question.id]),
        data={"score_id": score.id},
        content_type="application/json",
    )

    assert response.status_code == 404
