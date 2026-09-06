"""Read-only query helpers for quiz content."""

from django.db.models import Sum

from quizzes.models import Answer, Question, Quiz


def quiz_total_points(quiz):
    total = (
        Question.objects.filter(quiz=quiz).aggregate(total=Sum("points"))["total"]
    )
    return total or 0


def quiz_with_questions(quiz_id):
    return (
        Quiz.objects.filter(pk=quiz_id)
        .select_related("category")
        .prefetch_related("questions__answers")
        .first()
    )


def get_question_or_none(question_id):
    return Question.objects.filter(pk=question_id).select_related("quiz").first()


def get_answer_or_none(answer_id):
    return Answer.objects.filter(pk=answer_id).select_related("question").first()
