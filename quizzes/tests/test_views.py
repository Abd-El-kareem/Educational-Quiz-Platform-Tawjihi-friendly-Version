import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone

from quizzes.models import Quiz
from quizzes.services import create_quiz
from quizzes.tests.factories import CategoryFactory, make_quiz
from quizzes.tests.factories import UserFactory


@pytest.mark.django_db
def test_take_page_renders_questions(client, takeable_quiz):
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert response.status_code == 200
    assert b"Q1" in response.content
    assert b"quiz-widget" in response.content


@pytest.mark.django_db
def test_take_page_omits_timer_without_time_limit(client, takeable_quiz):
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b"timer-badge" not in response.content
    assert b"data-time-limit" not in response.content
    assert b"data-remaining" not in response.content


@pytest.mark.django_db
def test_take_page_shows_timer_for_timed_quiz(client, takeable_quiz):
    takeable_quiz.time_limit_minutes = 10
    takeable_quiz.save()
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b"timer-badge" in response.content
    assert b"Time Remaining" in response.content
    assert b'data-time-limit="10"' in response.content
    assert b'data-remaining="' in response.content


@pytest.mark.django_db
def test_take_page_lazily_marks_attempt_started(client, takeable_quiz):
    takeable_quiz.time_limit_minutes = 10
    takeable_quiz.save()
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert response.status_code == 200
    session = client.session
    assert f"quiz_started_{takeable_quiz.pk}" in session


@pytest.mark.django_db
def test_take_page_shows_zero_remaining_after_deadline(client, takeable_quiz):
    takeable_quiz.time_limit_minutes = 1
    takeable_quiz.save()
    client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    session = client.session
    session[f"quiz_started_{takeable_quiz.pk}"] = (
        timezone.now() - timedelta(hours=1)
    ).isoformat()
    session.save()
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b'data-remaining="0"' in response.content


@pytest.mark.django_db
def test_restart_resets_attempt_timer(client, takeable_quiz):
    takeable_quiz.time_limit_minutes = 1
    takeable_quiz.save()
    user = UserFactory()
    client.force_login(user)
    client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    session = client.session
    session[f"quiz_started_{takeable_quiz.pk}"] = (
        timezone.now() - timedelta(hours=1)
    ).isoformat()
    session.save()

    client.post(reverse("quizzes:quiz_restart", args=[takeable_quiz.pk]))
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b'data-remaining="0"' not in response.content
    assert b'data-remaining="' in response.content


@pytest.mark.django_db
def test_private_quiz_shows_gate_until_access(client, takeable_quiz):
    takeable_quiz.is_public = False
    takeable_quiz.access_code = "SECRET"
    takeable_quiz.save()

    gated = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b"Private Quiz" in gated.content
    assert b"quiz-widget" not in gated.content

    client.post(reverse("quizzes:quiz_access", args=[takeable_quiz.pk]), {"access_code": "SECRET"})
    unlocked = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b"quiz-widget" in unlocked.content


@pytest.mark.django_db
def test_locked_quiz_shows_score_and_hides_widget(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    for question in takeable_quiz.questions.all():
        correct = question.answers.get(is_correct=True)
        client.post(
            reverse("scoring_api:save_answer", args=[takeable_quiz.pk]),
            {"question_id": question.id, "answer_id": correct.id},
            content_type="application/json",
        )
    client.post(reverse("scoring_api:submit_quiz", args=[takeable_quiz.pk]))

    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b"quiz-widget" not in response.content
    assert b"Attempt 1 of 3 submitted" in response.content
    assert b"Review answers" in response.content


@pytest.mark.django_db
def test_take_page_hides_widget_when_attempts_exhausted(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    for _ in range(3):
        for question in takeable_quiz.questions.all():
            correct = question.answers.get(is_correct=True)
            client.post(
                reverse("scoring_api:save_answer", args=[takeable_quiz.pk]),
                {"question_id": question.id, "answer_id": correct.id},
                content_type="application/json",
            )
        client.post(reverse("scoring_api:submit_quiz", args=[takeable_quiz.pk]))

    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b"quiz-widget" not in response.content
    assert b"all 3 attempts" in response.content


@pytest.mark.django_db
def test_restart_clears_selections_and_shows_widget(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    for question in takeable_quiz.questions.all():
        correct = question.answers.get(is_correct=True)
        client.post(
            reverse("scoring_api:save_answer", args=[takeable_quiz.pk]),
            {"question_id": question.id, "answer_id": correct.id},
            content_type="application/json",
        )
    client.post(reverse("scoring_api:submit_quiz", args=[takeable_quiz.pk]))

    client.post(reverse("quizzes:quiz_restart", args=[takeable_quiz.pk]))
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert b"quiz-widget" in response.content
    assert b"checked" not in response.content


def _create_payload(**overrides):
    payload = {
        "title": "Built Quiz",
        "category": None,
        "is_public": "on",
        "questions-0-text": "Question One",
        "questions-0-points": "10",
        "questions-0-answers-0-text": "Right",
        "questions-0-answers-0-correct": "on",
        "questions-0-answers-1-text": "Wrong",
        "questions-1-text": "Question Two",
        "questions-1-points": "5",
        "questions-1-answers-0-text": "Yes",
        "questions-1-answers-0-correct": "on",
        "questions-1-answers-1-text": "No",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_create_quiz_via_form(client):
    user = UserFactory()
    category = CategoryFactory()
    client.force_login(user)
    response = client.post(reverse("quizzes:quiz_create"), _create_payload(category=category.pk))
    assert response.status_code == 302

    quiz = Quiz.objects.get(title="Built Quiz")
    assert quiz.category_id == category.pk
    assert quiz.questions.count() == 2
    assert sum(q.points for q in quiz.questions.all()) == 15


@pytest.mark.django_db
def test_create_quiz_via_form_persists_time_limit(client):
    user = UserFactory()
    category = CategoryFactory()
    client.force_login(user)
    response = client.post(
        reverse("quizzes:quiz_create"),
        _create_payload(category=category.pk, time_limit="45"),
    )
    assert response.status_code == 302
    assert Quiz.objects.get(title="Built Quiz").time_limit_minutes == 45


@pytest.mark.django_db
def test_create_quiz_via_form_defaults_no_time_limit(client):
    user = UserFactory()
    category = CategoryFactory()
    client.force_login(user)
    client.post(reverse("quizzes:quiz_create"), _create_payload(category=category.pk))
    assert Quiz.objects.get(title="Built Quiz").time_limit_minutes is None


@pytest.mark.parametrize("value", ["0", "181", "abc"])
@pytest.mark.django_db
def test_create_quiz_via_form_rejects_invalid_time_limit(client, value):
    user = UserFactory()
    category = CategoryFactory()
    client.force_login(user)
    response = client.post(
        reverse("quizzes:quiz_create"),
        _create_payload(category=category.pk, time_limit=value),
    )
    assert response.status_code == 200
    assert not Quiz.objects.exists()


@pytest.mark.django_db
def test_create_quiz_via_form_persists_math_enabled(client):
    user = UserFactory()
    category = CategoryFactory()
    client.force_login(user)
    payload = _create_payload(
        **{"category": category.pk, "questions-0-math": "on"}
    )
    response = client.post(reverse("quizzes:quiz_create"), payload)
    assert response.status_code == 302

    quiz = Quiz.objects.get(title="Built Quiz")
    first, second = list(quiz.questions.order_by("order"))
    assert first.math_enabled is True
    assert second.math_enabled is False


@pytest.mark.django_db
def test_take_page_renders_math_content_for_math_questions(client, takeable_quiz):
    takeable_quiz.questions.update(math_enabled=True)
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert response.status_code == 200
    assert b"math-content" in response.content
    assert b"katex" in response.content


@pytest.mark.django_db
def test_take_page_omits_math_markup_for_plain_questions(client, takeable_quiz):
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert response.status_code == 200
    assert b"math-content" not in response.content
    assert b"katex" not in response.content


KHATT_IMG = (
    '<img src="https://khatt.org/api?c=%D8%B3%20%3D%20%2F%D8%B9%D9%84%D9%89"'
    ' width="100" height="40" alt="س">'
)


@pytest.mark.django_db
def test_take_page_renders_khatt_images_in_arabic(client, takeable_quiz):
    takeable_quiz.questions.update(math_enabled=True, text=KHATT_IMG)
    response = client.get(
        reverse("quizzes:quiz_take", args=[takeable_quiz.pk]),
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert response.status_code == 200
    assert b"khatt-content" in response.content
    assert b"khatt.org/api?c=" in response.content
    assert b"katex" not in response.content


@pytest.mark.django_db
def test_take_page_renders_khatt_images_in_english(client, takeable_quiz):
    # Quizzes authored with the Arabic editor must display as images even when
    # the UI language is English (e.g. Arabic math for a student on EN).
    takeable_quiz.questions.update(math_enabled=True, text=KHATT_IMG)
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert response.status_code == 200
    assert b"khatt-content" in response.content
    assert b'<img src="https://khatt.org' in response.content
    assert b"khatt.org/api?c=" in response.content
    assert b"&lt;img" not in response.content


@pytest.mark.django_db
def test_take_page_omits_math_markup_for_plain_questions_in_arabic(client, takeable_quiz):
    response = client.get(
        reverse("quizzes:quiz_take", args=[takeable_quiz.pk]),
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert response.status_code == 200
    assert b'class="khatt-content"' not in response.content
    assert b'class="math-content"' not in response.content


@pytest.mark.django_db
def test_create_page_swaps_to_khatt_tools_in_arabic(client):
    user = UserFactory()
    client.force_login(user)
    response = client.get(reverse("quizzes:quiz_create"), HTTP_ACCEPT_LANGUAGE="ar")
    assert response.status_code == 200
    assert b"khatt_helper.js" in response.content
    assert b"latex_helper.js" not in response.content
    assert b"katex" not in response.content


@pytest.mark.django_db
def test_create_quiz_requires_login(client):
    response = client.get(reverse("quizzes:quiz_create"))
    assert response.status_code == 302
    assert "login" in response.url


@pytest.mark.django_db
def test_create_page_includes_latex_tools(client):
    user = UserFactory()
    client.force_login(user)
    response = client.get(reverse("quizzes:quiz_create"))
    assert response.status_code == 200
    assert b"latex_helper.js" in response.content
    assert b"katex" in response.content


@pytest.mark.django_db
def test_create_quiz_shows_validation_errors(client):
    user = UserFactory()
    category = CategoryFactory()
    client.force_login(user)
    payload = _create_payload(category=category.pk, title="")
    response = client.post(reverse("quizzes:quiz_create"), payload)
    assert response.status_code == 200
    assert not Quiz.objects.exists()


@pytest.mark.django_db
def test_private_quiz_via_form_requires_code(client):
    user = UserFactory()
    category = CategoryFactory()
    client.force_login(user)
    payload = _create_payload(category=category.pk, is_public="")
    response = client.post(reverse("quizzes:quiz_create"), payload)
    assert response.status_code == 200
    assert not Quiz.objects.exists()
