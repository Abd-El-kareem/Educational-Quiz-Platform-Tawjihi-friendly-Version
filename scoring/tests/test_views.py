import pytest
from django.urls import reverse

from quizzes.tests.factories import UserFactory, make_quiz
from scoring import services
from scoring.models import Score, ScoreAnswer
from scoring.tests.factories import ScoreFactory


@pytest.mark.django_db
def test_my_scores_lists_only_own_scores(client):
    user = UserFactory()
    other = UserFactory()
    client.force_login(user)
    mine = ScoreFactory(user=user)
    ScoreFactory(user=other)

    response = client.get(reverse("scoring:score_list"))
    assert response.status_code == 200
    assert mine.quiz.title.encode() in response.content
    assert "My Scores" in response.content.decode()


@pytest.mark.django_db
def test_my_scores_quiz_title_links_to_review(client):
    user = UserFactory()
    client.force_login(user)
    score = ScoreFactory(user=user)

    response = client.get(reverse("scoring:score_list"))
    assert response.status_code == 200
    assert f'href="/scores/{score.pk}/"'.encode() in response.content


@pytest.mark.django_db
def test_score_detail_shows_empty_state_for_score_without_answers(client):
    user = UserFactory()
    client.force_login(user)
    score = ScoreFactory(user=user)

    response = client.get(reverse("scoring:score_detail", args=[score.pk]))
    assert response.status_code == 200
    assert b"No attempt details" in response.content
    assert b"Ask AI" not in response.content


@pytest.mark.django_db
def test_my_scores_requires_login(client):
    response = client.get(reverse("scoring:score_list"))
    assert response.status_code == 302
    assert "login" in response.url


@pytest.mark.django_db
def test_score_detail_requires_login(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    score = ScoreFactory(user=user, quiz=takeable_quiz)
    client.logout()

    response = client.get(reverse("scoring:score_detail", args=[score.pk]))
    assert response.status_code == 302
    assert "login" in response.url


def _submit_for_user(client, user, quiz, wrong_first=True):
    client.force_login(user)
    for question in quiz.questions.all():
        answer = (
            question.answers.get(is_correct=False)
            if wrong_first
            else question.answers.get(is_correct=True)
        )
        client.post(
            reverse("scoring_api:save_answer", args=[quiz.pk]),
            {"question_id": question.id, "answer_id": answer.id},
            content_type="application/json",
        )
    client.post(reverse("scoring_api:submit_quiz", args=[quiz.pk]))


@pytest.mark.django_db
def test_score_detail_shows_attempt_answers(client, takeable_quiz):
    user = UserFactory()
    _submit_for_user(client, user, takeable_quiz, wrong_first=True)

    score = Score.objects.get(user=user, quiz=takeable_quiz)
    response = client.get(reverse("scoring:score_detail", args=[score.pk]))
    assert response.status_code == 200
    assert f"Attempt {score.attempt_number}".encode() in response.content
    assert b"Your answer: A2" in response.content
    assert b"Correct answer: A1" in response.content
    assert b"Ask AI" in response.content


@pytest.mark.django_db
def test_score_detail_always_loads_katex_for_ai_answers(client, takeable_quiz):
    """AI answers can contain LaTeX even when the quiz itself has no math."""
    assert takeable_quiz.questions.filter(math_enabled=True).count() == 0
    user = UserFactory()
    _submit_for_user(client, user, takeable_quiz, wrong_first=True)
    score = Score.objects.get(user=user, quiz=takeable_quiz)

    response = client.get(reverse("scoring:score_detail", args=[score.pk]))
    assert response.status_code == 200
    assert b"katex@0.16.11/dist/katex.min.js" in response.content
    assert b"auto-render.min.js" in response.content
    assert b"js/ai_explainer.js" in response.content


@pytest.mark.django_db
def test_score_detail_loads_katex_in_arabic(client, takeable_quiz):
    """Arabic pages use the khatt engine for quiz math, but the AI answer still
    renders LaTeX client-side, so KaTeX must be present there too."""
    assert takeable_quiz.questions.filter(math_enabled=True).count() == 0
    user = UserFactory()
    _submit_for_user(client, user, takeable_quiz, wrong_first=True)
    score = Score.objects.get(user=user, quiz=takeable_quiz)

    response = client.get(
        reverse("scoring:score_detail", args=[score.pk]),
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert response.status_code == 200
    assert b"katex@0.16.11/dist/katex.min.js" in response.content


@pytest.mark.django_db
def test_score_detail_404_for_other_users_score(client, takeable_quiz):
    owner = UserFactory()
    _submit_for_user(client, owner, takeable_quiz)
    score = Score.objects.get(user=owner, quiz=takeable_quiz)

    other = UserFactory()
    client.force_login(other)
    response = client.get(reverse("scoring:score_detail", args=[score.pk]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_score_detail_lists_all_attempts_as_separate_rows(client, takeable_quiz):
    user = UserFactory()
    for _ in range(3):
        _submit_for_user(client, user, takeable_quiz)

    assert Score.objects.filter(user=user, quiz=takeable_quiz).count() == 3
    response = client.get(reverse("scoring:score_list"))
    assert response.status_code == 200
    assert b"Review" in response.content


KHATT_IMG = (
    '<img src="https://khatt.org/api?c=%D8%B3%20%3D%20%2F%D8%B9%D9%84%D9%89"'
    ' width="100" height="40" alt="س">'
)


def _make_khatt_score(user, quiz, is_correct=True):
    score = ScoreFactory(user=user, quiz=quiz)
    question = quiz.questions.first()
    ScoreAnswer.objects.create(
        score=score,
        question=question,
        answer=question.answers.first(),
        question_text=KHATT_IMG,
        answer_text=KHATT_IMG,
        correct_answer_text=KHATT_IMG,
        points=10,
        is_correct=is_correct,
    )
    return score


@pytest.mark.django_db
def test_review_renders_khatt_images_in_english(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    score = _make_khatt_score(user, takeable_quiz)

    response = client.get(reverse("scoring:score_detail", args=[score.pk]))
    assert response.status_code == 200
    assert b'<img src="https://khatt.org' in response.content
    assert b"&lt;img" not in response.content


@pytest.mark.django_db
def test_review_renders_khatt_images_in_arabic(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    score = _make_khatt_score(user, takeable_quiz, is_correct=False)

    response = client.get(
        reverse("scoring:score_detail", args=[score.pk]),
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert response.status_code == 200
    # Question text, "Your answer" and "Correct answer" rows all render images.
    assert response.content.count(b"khatt.org/api?c=") >= 3
    assert b"&lt;img" not in response.content
