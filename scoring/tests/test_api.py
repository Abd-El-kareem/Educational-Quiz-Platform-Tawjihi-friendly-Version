import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone

from scoring.models import Score
from quizzes.tests.factories import UserFactory


def answers_url(quiz_id):
    return reverse("scoring_api:save_answer", args=[quiz_id])


def submit_url(quiz_id):
    return reverse("scoring_api:submit_quiz", args=[quiz_id])


def questions_of(quiz):
    return list(quiz.questions.all())


def answer_ids(question):
    return {a.text: a.id for a in question.answers.all()}


@pytest.mark.django_db
def test_guest_save_answer_returns_ok(client, takeable_quiz):
    question = takeable_quiz.questions.first()
    ids = answer_ids(question)
    response = client.post(
        answers_url(takeable_quiz.id),
        {"question_id": question.id, "answer_id": ids["A1"]},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.data["status"] == "ok"


@pytest.mark.django_db
def test_guest_full_submit_flow(client, takeable_quiz):
    for question in questions_of(takeable_quiz):
        ids = answer_ids(question)
        client.post(
            answers_url(takeable_quiz.id),
            {"question_id": question.id, "answer_id": ids["A1"] if "A1" in ids else ids["B2"]},
            content_type="application/json",
        )
    response = client.post(submit_url(takeable_quiz.id))
    assert response.status_code == 200
    assert response.data == {"earned": 15, "total": 15, "correct": 2}

    second = client.post(submit_url(takeable_quiz.id))
    assert second.status_code == 409


@pytest.mark.django_db
def test_submit_reports_unanswered_questions(client, takeable_quiz):
    response = client.post(submit_url(takeable_quiz.id))
    assert response.status_code == 400
    assert len(response.data["unanswered"]) == 2


@pytest.mark.django_db
def test_authenticated_user_score_persisted(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    for question in questions_of(takeable_quiz):
        ids = answer_ids(question)
        client.post(
            answers_url(takeable_quiz.id),
            {"question_id": question.id, "answer_id": ids["A1"] if "A1" in ids else ids["B2"]},
            content_type="application/json",
        )
    client.post(submit_url(takeable_quiz.id))
    assert Score.objects.filter(user=user, quiz=takeable_quiz).count() == 1


@pytest.mark.django_db
def test_authenticated_user_can_submit_three_times_then_blocked(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    for _ in range(3):
        for question in questions_of(takeable_quiz):
            ids = answer_ids(question)
            client.post(
                answers_url(takeable_quiz.id),
                {"question_id": question.id, "answer_id": ids["A1"] if "A1" in ids else ids["B2"]},
                content_type="application/json",
            )
        response = client.post(submit_url(takeable_quiz.id))
        assert response.status_code == 200

    assert Score.objects.filter(user=user, quiz=takeable_quiz).count() == 3
    assert list(
        Score.objects.filter(user=user, quiz=takeable_quiz)
        .order_by("attempt_number")
        .values_list("attempt_number", flat=True)
    ) == [1, 2, 3]

    fourth = client.post(submit_url(takeable_quiz.id))
    assert fourth.status_code == 409


@pytest.mark.django_db
def test_private_quiz_blocks_until_access_code(client, takeable_quiz):
    takeable_quiz.is_public = False
    takeable_quiz.access_code = "SECRET"
    takeable_quiz.save()
    question = takeable_quiz.questions.first()
    ids = answer_ids(question)

    blocked = client.post(
        answers_url(takeable_quiz.id),
        {"question_id": question.id, "answer_id": ids["A1"]},
        content_type="application/json",
    )
    assert blocked.status_code == 403

    client.post(reverse("quizzes:quiz_access", args=[takeable_quiz.id]), {"access_code": "SECRET"})
    allowed = client.post(
        answers_url(takeable_quiz.id),
        {"question_id": question.id, "answer_id": ids["A1"]},
        content_type="application/json",
    )
    assert allowed.status_code == 200


@pytest.mark.django_db
def test_private_quiz_wrong_code_not_granted(client, takeable_quiz):
    takeable_quiz.is_public = False
    takeable_quiz.access_code = "SECRET"
    takeable_quiz.save()
    client.post(reverse("quizzes:quiz_access", args=[takeable_quiz.id]), {"access_code": "WRONG"})
    question = takeable_quiz.questions.first()
    ids = answer_ids(question)
    response = client.post(
        answers_url(takeable_quiz.id),
        {"question_id": question.id, "answer_id": ids["A1"]},
        content_type="application/json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_save_answer_rejects_bad_answer(client, takeable_quiz):
    question = takeable_quiz.questions.first()
    response = client.post(
        answers_url(takeable_quiz.id),
        {"question_id": question.id, "answer_id": 999999},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_missing_quiz_returns_404(client):
    response = client.post(submit_url(999999))
    assert response.status_code == 404


def _timed(client, quiz, minutes):
    quiz.time_limit_minutes = minutes
    quiz.save()
    client.get(reverse("quizzes:quiz_take", args=[quiz.id]))
    session = client.session
    session[f"quiz_started_{quiz.id}"] = (
        timezone.now() - timedelta(hours=1)
    ).isoformat()
    session.save()
    return quiz


@pytest.mark.django_db
def test_save_answer_returns_410_after_time_expires(client, takeable_quiz):
    _timed(client, takeable_quiz, 1)
    question = takeable_quiz.questions.first()
    ids = answer_ids(question)
    response = client.post(
        answers_url(takeable_quiz.id),
        {"question_id": question.id, "answer_id": ids["A1"]},
        content_type="application/json",
    )
    assert response.status_code == 410
    assert response.data["detail"]


@pytest.mark.django_db
def test_submit_timed_out_finalizes_unanswered(client, takeable_quiz):
    _timed(client, takeable_quiz, 1)
    response = client.post(
        submit_url(takeable_quiz.id),
        {"timed_out": True},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.data == {"earned": 0, "total": 15, "correct": 0}

    second = client.post(submit_url(takeable_quiz.id))
    assert second.status_code == 409


@pytest.mark.django_db
def test_submit_timed_out_flag_ignored_before_deadline(client, takeable_quiz):
    takeable_quiz.time_limit_minutes = 30
    takeable_quiz.save()
    client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.id]))
    response = client.post(
        submit_url(takeable_quiz.id),
        {"timed_out": True},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert len(response.data["unanswered"]) == 2
