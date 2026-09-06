"""Read-only query helpers for scoring."""

from scoring.models import Score, SelectedAnswer


def user_scores(user):
    return (
        Score.objects.filter(user=user)
        .select_related("quiz", "quiz__category")
        .order_by("-completed_at")
    )


def user_score_for_quiz(user, quiz):
    return Score.objects.filter(user=user, quiz=quiz).first()


def user_attempts(user, quiz):
    """All graded attempts for a user on a quiz, oldest first."""
    return Score.objects.filter(user=user, quiz=quiz).order_by("attempt_number")


def score_with_answers(score):
    return (
        Score.objects.filter(pk=score.pk)
        .select_related("quiz", "quiz__category")
        .prefetch_related("answers")
        .first()
    )


def selected_map(user, store, quiz):
    """Current {question_id: answer_id} selections for a user/guest on a quiz."""
    if user.is_authenticated:
        selections = SelectedAnswer.objects.filter(user=user, quiz=quiz)
        return {str(s.question_id): str(s.answer_id) for s in selections}
    return store.get_answers(quiz.id)


def user_locked_result(user, store, quiz):
    if user.is_authenticated:
        score = user_score_for_quiz(user, quiz)
        if score is None:
            return None
        return {"earned": score.earned, "total": score.total}
    return store.get_lock(quiz.id)
