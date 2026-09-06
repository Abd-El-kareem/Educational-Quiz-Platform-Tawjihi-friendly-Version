"""Write-side logic for quiz content."""

import logging

from django.conf import settings
from django.db import transaction

from core.translations import t
from quizzes.models import Answer, Question, Quiz

logger = logging.getLogger(__name__)


class QuizValidationError(ValueError):
    pass


def _clean_question(index, raw, lang="en"):
    text = (raw.get("text") or "").strip()
    if not text:
        raise QuizValidationError(t("Question {n}: text is required.", lang, n=index + 1))

    try:
        points = int(raw.get("points", 1))
    except (TypeError, ValueError):
        raise QuizValidationError(t("Question {n}: points must be a number.", lang, n=index + 1))
    if points < 1:
        raise QuizValidationError(t("Question {n}: points must be at least 1.", lang, n=index + 1))

    answers = raw.get("answers") or []
    if len(answers) < settings.MIN_ANSWERS_PER_QUESTION:
        raise QuizValidationError(
            t(
                "Question {n}: at least {m} answers are required.",
                lang,
                n=index + 1,
                m=settings.MIN_ANSWERS_PER_QUESTION,
            )
        )

    cleaned_answers = []
    has_correct = False
    for a_index, answer in enumerate(answers):
        text = (answer.get("text") or "").strip()
        if not text:
            raise QuizValidationError(
                t("Question {n}, answer {m}: text is required.", lang, n=index + 1, m=a_index + 1)
            )
        is_correct = bool(answer.get("is_correct"))
        has_correct = has_correct or is_correct
        cleaned_answers.append({"text": text, "is_correct": is_correct})

    if not has_correct:
        raise QuizValidationError(
            t("Question {n}: at least one answer must be marked correct.", lang, n=index + 1)
        )

    return {
        "text": raw["text"].strip(),
        "points": points,
        "image": raw.get("image"),
        "math_enabled": bool(raw.get("math_enabled")),
        "answers": cleaned_answers,
    }


def create_quiz(*, created_by, title, category, is_public, access_code=None, time_limit=None, questions, lang="en"):
    """Create a quiz atomically and validate content invariants.

    The quiz's total points are never stored; they are always derived from the
    sum of its questions' points (see quizzes.selectors.quiz_total_points).
    """
    title = (title or "").strip()
    if not title:
        raise QuizValidationError(t("Quiz title is required.", lang))

    if time_limit is not None:
        try:
            time_limit = int(time_limit)
        except (TypeError, ValueError):
            raise QuizValidationError(t("Time limit must be a whole number of minutes.", lang))
        if time_limit < 1 or time_limit > settings.MAX_QUIZ_TIME_LIMIT_MINUTES:
            raise QuizValidationError(t("Time limit must be between 1 and {n} minutes.", lang, n=settings.MAX_QUIZ_TIME_LIMIT_MINUTES))

    questions = list(questions or [])
    if not questions:
        raise QuizValidationError(t("A quiz must have at least one question.", lang))
    if len(questions) > settings.MAX_QUESTIONS_PER_QUIZ:
        raise QuizValidationError(
            t("A quiz can have at most {n} questions.", lang, n=settings.MAX_QUESTIONS_PER_QUIZ)
        )

    cleaned_questions = [_clean_question(i, q, lang) for i, q in enumerate(questions)]

    if not is_public and not (access_code or "").strip():
        raise QuizValidationError(t("A private quiz requires an access code.", lang))
    access_code = (access_code or "").strip() if not is_public else ""

    with transaction.atomic():
        quiz = Quiz.objects.create(
            title=title,
            category=category,
            is_public=is_public,
            access_code=access_code,
            time_limit_minutes=time_limit,
            created_by=created_by,
        )
        for order, question in enumerate(cleaned_questions):
            q = Question.objects.create(
                quiz=quiz,
                text=question["text"],
                points=question["points"],
                image=question.get("image"),
                math_enabled=question["math_enabled"],
                order=order,
            )
            Answer.objects.bulk_create(
                Answer(
                    question=q,
                    text=answer["text"],
                    is_correct=answer["is_correct"],
                    order=a_index,
                )
                for a_index, answer in enumerate(question["answers"])
            )
    logger.info(
        "Created quiz %r with %d question(s), %d LaTeX-enabled",
        quiz.title,
        len(cleaned_questions),
        sum(1 for q in cleaned_questions if q["math_enabled"]),
    )
    return quiz
