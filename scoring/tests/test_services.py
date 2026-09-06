import pytest
from datetime import timedelta
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.utils import timezone

from core.sessions import QuizSessionStore
from quizzes.tests.factories import make_quiz
from scoring import services
from scoring.models import Score, SelectedAnswer
from scoring.tests.factories import ScoreFactory
from quizzes.tests.factories import UserFactory

from types import SimpleNamespace


class FakeSession(dict):
    modified = False


def guest_store():
    return QuizSessionStore(SimpleNamespace(session=FakeSession()))


def get_quiz(quiz, index):
    return quiz.questions.all()[index]


def correct_answer(question):
    return question.answers.get(is_correct=True)


def wrong_answer(question):
    return question.answers.get(is_correct=False)


@pytest.mark.django_db
def test_record_answer_for_guest_uses_session(takeable_quiz):
    store = guest_store()
    question = get_quiz(takeable_quiz, 0)
    services.record_answer(
        user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
        question_id=question.id, answer_id=correct_answer(question).id,
    )
    assert store.get_answer(takeable_quiz.id, question.id) == str(correct_answer(question).id)


@pytest.mark.django_db
def test_record_answer_for_user_persists_selection(takeable_quiz):
    user = UserFactory()
    question = get_quiz(takeable_quiz, 0)
    services.record_answer(
        user=user, store=guest_store(), quiz_id=takeable_quiz.id,
        question_id=question.id, answer_id=correct_answer(question).id,
    )
    selection = SelectedAnswer.objects.get(user=user, quiz=takeable_quiz, question=question)
    assert selection.answer_id == correct_answer(question).id


@pytest.mark.django_db
def test_record_answer_updates_existing_selection(takeable_quiz):
    user = UserFactory()
    question = get_quiz(takeable_quiz, 0)
    store = guest_store()
    services.record_answer(user=user, store=store, quiz_id=takeable_quiz.id,
                           question_id=question.id, answer_id=correct_answer(question).id)
    services.record_answer(user=user, store=store, quiz_id=takeable_quiz.id,
                           question_id=question.id, answer_id=wrong_answer(question).id)
    assert SelectedAnswer.objects.filter(user=user, question=question).count() == 1


@pytest.mark.django_db
def test_record_answer_rejects_answer_from_other_question(takeable_quiz):
    store = guest_store()
    question = get_quiz(takeable_quiz, 1)
    other = get_quiz(takeable_quiz, 0)
    with pytest.raises(ValueError):
        services.record_answer(
            user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
            question_id=question.id, answer_id=correct_answer(other).id,
        )


@pytest.mark.django_db
def test_private_quiz_requires_access(takeable_quiz):
    takeable_quiz.is_public = False
    takeable_quiz.access_code = "X"
    takeable_quiz.save()
    store = guest_store()
    question = get_quiz(takeable_quiz, 0)
    with pytest.raises(services.AccessDeniedError):
        services.record_answer(
            user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
            question_id=question.id, answer_id=correct_answer(question).id,
        )

    store.grant_access(takeable_quiz.id)
    services.record_answer(
        user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
        question_id=question.id, answer_id=correct_answer(question).id,
    )


def _answer_all(quiz, store, user, wrong_first=True):
    for question in quiz.questions.all():
        answer = wrong_answer(question) if wrong_first else correct_answer(question)
        services.record_answer(
            user=user, store=store, quiz_id=quiz.id,
            question_id=question.id, answer_id=answer.id,
        )


@pytest.mark.django_db
def test_submit_computes_score_for_guest(takeable_quiz):
    store = guest_store()
    _answer_all(takeable_quiz, store, AnonymousUser(), wrong_first=False)
    result = services.submit_quiz(user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id)
    assert result == {"earned": 15, "total": 15, "correct": 2}
    assert store.is_locked(takeable_quiz.id)
    assert store.get_lock(takeable_quiz.id) == {"earned": 15, "total": 15}


@pytest.mark.django_db
def test_submit_computes_partial_score(takeable_quiz):
    store = guest_store()
    first = get_quiz(takeable_quiz, 0)
    second = get_quiz(takeable_quiz, 1)
    services.record_answer(
        user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
        question_id=first.id, answer_id=correct_answer(first).id,
    )
    services.record_answer(
        user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
        question_id=second.id, answer_id=wrong_answer(second).id,
    )
    result = services.submit_quiz(user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id)
    assert result == {"earned": 10, "total": 15, "correct": 1}


@pytest.mark.django_db
def test_submit_rejects_unanswered_questions(takeable_quiz):
    store = guest_store()
    with pytest.raises(services.UnansweredQuestionsError) as excinfo:
        services.submit_quiz(user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id)
    assert len(excinfo.value.unanswered_question_ids) == 2


@pytest.mark.django_db
def test_submit_persists_score_for_user(takeable_quiz):
    user = UserFactory()
    store = guest_store()
    _answer_all(takeable_quiz, store, user, wrong_first=False)
    result = services.submit_quiz(user=user, store=store, quiz_id=takeable_quiz.id)
    score = Score.objects.get(user=user, quiz=takeable_quiz)
    assert score.earned == result["earned"]
    assert score.total == 15
    assert score.attempt_number == 1


@pytest.mark.django_db
def test_user_can_submit_up_to_three_attempts(takeable_quiz):
    user = UserFactory()
    store = guest_store()
    _answer_all(takeable_quiz, store, user, wrong_first=False)
    for expected in (1, 2, 3):
        result = services.submit_quiz(user=user, store=store, quiz_id=takeable_quiz.id)
        score = Score.objects.get(
            user=user, quiz=takeable_quiz, attempt_number=expected
        )
        assert score.earned == result["earned"]
        assert score.total == 15
    with pytest.raises(services.AlreadySubmittedError):
        services.submit_quiz(user=user, store=store, quiz_id=takeable_quiz.id)


@pytest.mark.django_db
def test_submit_records_score_answer_snapshots(takeable_quiz):
    user = UserFactory()
    store = guest_store()
    _answer_all(takeable_quiz, store, user, wrong_first=True)
    services.submit_quiz(user=user, store=store, quiz_id=takeable_quiz.id)

    score = Score.objects.get(user=user, quiz=takeable_quiz)
    assert score.answers.count() == 2
    q1 = get_quiz(takeable_quiz, 0)
    sa1 = score.answers.get(question=q1)
    assert sa1.answer_text == wrong_answer(q1).text
    assert sa1.correct_answer_text == correct_answer(q1).text
    assert sa1.question_text == q1.text
    assert sa1.points == q1.points
    assert sa1.is_correct is False


@pytest.mark.django_db
def test_start_attempt_clears_user_selections(takeable_quiz):
    user = UserFactory()
    store = guest_store()
    _answer_all(takeable_quiz, store, user, wrong_first=False)
    assert SelectedAnswer.objects.filter(user=user, quiz=takeable_quiz).count() == 2

    services.start_attempt(user=user, store=store, quiz_id=takeable_quiz.id)
    assert SelectedAnswer.objects.filter(user=user, quiz=takeable_quiz).count() == 0


@pytest.mark.django_db
def test_start_attempt_clears_guest_answers(takeable_quiz):
    store = guest_store()
    _answer_all(takeable_quiz, store, AnonymousUser(), wrong_first=False)
    assert store.get_answers(takeable_quiz.id)

    services.start_attempt(user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id)
    assert not store.get_answers(takeable_quiz.id)


@pytest.mark.django_db
def test_submit_locked_for_guest_once(takeable_quiz):
    store = guest_store()
    _answer_all(takeable_quiz, store, AnonymousUser(), wrong_first=False)
    services.submit_quiz(user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id)
    with pytest.raises(services.AlreadySubmittedError):
        services.submit_quiz(user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id)


@pytest.mark.django_db
def test_record_answer_rejected_after_attempts_exhausted(takeable_quiz):
    user = UserFactory()
    store = guest_store()
    _answer_all(takeable_quiz, store, user, wrong_first=False)
    for _ in range(3):
        services.submit_quiz(user=user, store=store, quiz_id=takeable_quiz.id)
    question = get_quiz(takeable_quiz, 0)
    with pytest.raises(services.AlreadySubmittedError):
        services.record_answer(
            user=user, store=store, quiz_id=takeable_quiz.id,
            question_id=question.id, answer_id=correct_answer(question).id,
        )


def _expire(store, quiz, minutes=60):
    """Mark the attempt started, then rewind the timestamp so it has expired."""
    store.mark_started(quiz.id)
    store._session[f"quiz_started_{quiz.id}"] = (
        timezone.now() - timedelta(minutes=minutes)
    ).isoformat()
    store._session.modified = True


def _timed(takeable_quiz, minutes):
    takeable_quiz.time_limit_minutes = minutes
    takeable_quiz.save()
    return takeable_quiz


@pytest.mark.django_db
def test_remaining_seconds_is_none_without_time_limit(takeable_quiz):
    assert services.remaining_seconds(guest_store(), takeable_quiz) is None


@pytest.mark.django_db
def test_remaining_seconds_full_window_when_not_started(takeable_quiz):
    _timed(takeable_quiz, 10)
    assert services.remaining_seconds(guest_store(), takeable_quiz) == 600


@pytest.mark.django_db
def test_remaining_seconds_after_start(takeable_quiz):
    _timed(takeable_quiz, 10)
    store = guest_store()
    store.mark_started(takeable_quiz.id)
    remaining = services.remaining_seconds(store, takeable_quiz)
    assert 0 < remaining <= 600


@pytest.mark.django_db
def test_record_answer_allowed_before_deadline(takeable_quiz):
    _timed(takeable_quiz, 30)
    store = guest_store()
    store.mark_started(takeable_quiz.id)
    question = get_quiz(takeable_quiz, 0)
    services.record_answer(
        user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
        question_id=question.id, answer_id=correct_answer(question).id,
    )


@pytest.mark.django_db
def test_record_answer_rejected_after_deadline(takeable_quiz):
    _timed(takeable_quiz, 1)
    store = guest_store()
    _expire(store, takeable_quiz)
    question = get_quiz(takeable_quiz, 0)
    with pytest.raises(services.TimeExpiredError):
        services.record_answer(
            user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
            question_id=question.id, answer_id=correct_answer(question).id,
        )


@pytest.mark.django_db
def test_submit_timed_out_finalizes_unanswered(takeable_quiz):
    _timed(takeable_quiz, 1)
    store = guest_store()
    _expire(store, takeable_quiz)
    result = services.submit_quiz(
        user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id, timed_out=True
    )
    assert result == {"earned": 0, "total": 15, "correct": 0}
    assert store.is_locked(takeable_quiz.id)
    with pytest.raises(services.AlreadySubmittedError):
        services.submit_quiz(
            user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id, timed_out=True
        )


@pytest.mark.django_db
def test_submit_timed_out_flag_ignored_before_deadline(takeable_quiz):
    _timed(takeable_quiz, 30)
    store = guest_store()
    store.mark_started(takeable_quiz.id)
    with pytest.raises(services.UnansweredQuestionsError):
        services.submit_quiz(
            user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id, timed_out=True
        )


@pytest.mark.django_db
def test_submit_still_requires_answers_with_time_limit(takeable_quiz):
    _timed(takeable_quiz, 30)
    store = guest_store()
    store.mark_started(takeable_quiz.id)
    with pytest.raises(services.UnansweredQuestionsError):
        services.submit_quiz(
            user=AnonymousUser(), store=store, quiz_id=takeable_quiz.id,
        )
