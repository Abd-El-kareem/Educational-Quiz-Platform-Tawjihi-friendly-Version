"""Write-side logic for quiz attempts, scoring, and lock-in.

Guests persist attempt state through ``core.sessions.QuizSessionStore``;
authenticated users persist through ``SelectedAnswer`` and ``Score``.
"""

import math

from django.db import IntegrityError, transaction
from django.utils import timezone

from quizzes import selectors as quiz_selectors
from scoring import selectors as scoring_selectors
from scoring.models import Score, ScoreAnswer, SelectedAnswer

MAX_ATTEMPTS = 3


class QuizNotFoundError(ValueError):
    pass


class AccessDeniedError(PermissionError):
    pass


class AlreadySubmittedError(ValueError):
    pass


class TimeExpiredError(ValueError):
    """Raised when a timed quiz attempt has exceeded its time limit."""


class UnansweredQuestionsError(ValueError):
    def __init__(self, unanswered_question_ids):
        self.unanswered_question_ids = unanswered_question_ids
        super().__init__(
            "Not all questions have been answered: %s" % unanswered_question_ids
        )


def remaining_seconds(store, quiz):
    """Seconds left in the attempt window, or None when no time limit applies.

    A missing/unreliable start timestamp (e.g. a legacy session) disables
    server-side enforcement but still returns a full-window fallback when the
    quiz carries a time limit, so clients can run a best-effort countdown.
    """
    time_limit = getattr(quiz, "time_limit_minutes", None)
    if not time_limit:
        return None
    start = store.started_at(quiz.id)
    if start is None:
        return time_limit * 60
    elapsed = (timezone.now() - start).total_seconds()
    return max(0, int(math.ceil(time_limit * 60 - elapsed)))


def _time_expired(store, quiz):
    remaining = remaining_seconds(store, quiz)
    return remaining is not None and remaining <= 0


def attempt_count(*, user, quiz_id):
    return Score.objects.filter(user=user, quiz_id=quiz_id).count()


def attempts_left(*, user, quiz_id):
    return MAX_ATTEMPTS - attempt_count(user=user, quiz_id=quiz_id)


def _is_locked(*, user, store, quiz_id):
    if user.is_authenticated:
        return attempt_count(user=user, quiz_id=quiz_id) >= MAX_ATTEMPTS
    return store.is_locked(quiz_id)


def _require_takeable(*, user, store, quiz):
    if not quiz.is_public and not store.has_access(quiz.id):
        raise AccessDeniedError("This private quiz requires a valid access code.")
    if _is_locked(user=user, store=store, quiz_id=quiz.id):
        raise AlreadySubmittedError(
            "You have already used all %d attempts for this quiz." % MAX_ATTEMPTS
        )
    return True


def record_answer(*, user, store, quiz_id, question_id, answer_id):
    """Persist a single answer selection immediately (no final submit)."""
    quiz = quiz_selectors.quiz_with_questions(quiz_id)
    if quiz is None:
        raise QuizNotFoundError("Quiz not found.")
    _require_takeable(user=user, store=store, quiz=quiz)
    if _time_expired(store, quiz):
        raise TimeExpiredError("Time's up. Your answers were submitted.")

    answer = quiz_selectors.get_answer_or_none(answer_id)
    if answer is None or answer.question_id != int(question_id):
        raise ValueError("The answer does not belong to this question.")

    if user.is_authenticated:
        SelectedAnswer.objects.update_or_create(
            user=user, quiz_id=quiz_id, question_id=question_id,
            defaults={"answer_id": answer_id},
        )
    else:
        store.set_answer(quiz_id, question_id, answer_id)


def _selected_map(user, store, quiz):
    return scoring_selectors.selected_map(user, store, quiz)


def question_results(quiz, selected_map):
    """Per-question outcome map {question_id: {...}} for a selection map."""
    results = {}
    for question in quiz.questions.all().prefetch_related("answers"):
        selected = selected_map.get(str(question.id))
        answer = (
            question.answers.filter(pk=selected).first() if selected else None
        )
        is_correct = bool(answer and answer.is_correct)
        results[question.id] = {
            "question": question,
            "answer": answer,
            "answer_text": answer.text if answer else "",
            "points": question.points,
            "is_correct": is_correct,
        }
    return results


def compute_score(quiz, selected_map):
    """Compute earned/total/correct from {question_id: answer_id} selections."""
    earned = 0
    correct = 0
    total = 0
    for question_id, r in question_results(quiz, selected_map).items():
        total += r["points"]
        if r["is_correct"]:
            earned += r["points"]
            correct += 1
    return {"earned": earned, "total": total, "correct": correct}


def _create_score_answers(score, question_results_map):
    for r in question_results_map.values():
        correct = next(
            (a for a in r["question"].answers.all() if a.is_correct), None
        )
        ScoreAnswer.objects.create(
            score=score,
            question=r["question"],
            answer=r["answer"],
            question_text=r["question"].text,
            answer_text=r["answer_text"],
            correct_answer_text=correct.text if correct else "",
            points=r["points"],
            is_correct=r["is_correct"],
        )


def submit_quiz(*, user, store, quiz_id, timed_out=False):
    """Compute the score, record the attempt, and lock it in.

    Authenticated users may submit up to ``MAX_ATTEMPTS`` times; each attempt
    gets its own ``Score`` plus per-question ``ScoreAnswer`` snapshots. Guests
    keep the previous single-lock behaviour.

    ``timed_out`` is honoured only when the attempt has actually exceeded its
    time limit; it lets the auto-submit finalize the attempt even if some
    questions were left unanswered.
    """
    quiz = quiz_selectors.quiz_with_questions(quiz_id)
    if quiz is None:
        raise QuizNotFoundError("Quiz not found.")
    _require_takeable(user=user, store=store, quiz=quiz)

    selected_map = _selected_map(user, store, quiz)

    question_ids = [str(q.id) for q in quiz.questions.all()]
    unanswered = [int(qid) for qid in question_ids if qid not in selected_map]
    expired = timed_out and _time_expired(store, quiz)
    if unanswered and not expired:
        raise UnansweredQuestionsError(unanswered)

    result = compute_score(quiz, selected_map)
    store.clear_started(quiz_id)

    if user.is_authenticated:
        try:
            with transaction.atomic():
                attempt_number = attempt_count(user=user, quiz_id=quiz.id) + 1
                score = Score.objects.create(
                    user=user,
                    quiz=quiz,
                    earned=result["earned"],
                    total=result["total"],
                    attempt_number=attempt_number,
                )
                _create_score_answers(score, question_results(quiz, selected_map))
        except IntegrityError as exc:
            raise AlreadySubmittedError(
                "You have already used all %d attempts for this quiz." % MAX_ATTEMPTS
            ) from exc
    else:
        store.lock(quiz_id, result["earned"], result["total"])

    return result


def start_attempt(*, user, store, quiz_id):
    """Clear in-progress selections and mark a fresh attempt as started."""
    quiz = quiz_selectors.quiz_with_questions(quiz_id)
    if quiz is None:
        raise QuizNotFoundError("Quiz not found.")
    if user.is_authenticated:
        SelectedAnswer.objects.filter(user=user, quiz_id=quiz_id).delete()
    else:
        store.clear_answers(quiz_id)
    store.mark_started(quiz_id)
