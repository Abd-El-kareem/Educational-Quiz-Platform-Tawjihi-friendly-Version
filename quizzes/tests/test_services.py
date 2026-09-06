import pytest
from django.conf import settings
from django.db.models import Sum

from quizzes import selectors
from quizzes.models import Quiz
from quizzes.services import QuizValidationError, create_quiz
from quizzes.tests.factories import CategoryFactory


def base_payload(category, **overrides):
    payload = {
        "created_by": None,
        "title": "My Quiz",
        "category": category,
        "is_public": True,
        "access_code": None,
        "questions": [
            {
                "text": "Q1",
                "points": 10,
                "answers": [
                    {"text": "A", "is_correct": True},
                    {"text": "B", "is_correct": False},
                ],
            },
            {
                "text": "Q2",
                "points": 5,
                "answers": [
                    {"text": "C", "is_correct": False},
                    {"text": "D", "is_correct": True},
                ],
            },
        ],
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_create_quiz_builds_content():
    category = CategoryFactory()
    quiz = create_quiz(**base_payload(category))
    assert quiz.title == "My Quiz"
    assert Quiz.objects.count() == 1
    assert quiz.questions.count() == 2
    assert quiz.questions.first().answers.count() == 2
    assert quiz.questions.filter(answers__is_correct=True).count() == 2


@pytest.mark.django_db
def test_total_points_equals_sum_of_question_points():
    category = CategoryFactory()
    quiz = create_quiz(**base_payload(category))
    assert selectors.quiz_total_points(quiz) == 15
    assert quiz.questions.aggregate(sum=Sum("points"))["sum"] == 15


@pytest.mark.django_db
def test_create_quiz_persists_math_enabled():
    category = CategoryFactory()
    quiz = create_quiz(
        **base_payload(
            category,
            questions=[
                {
                    "text": "\\$E = mc^2\\$",
                    "points": 10,
                    "math_enabled": True,
                    "answers": [
                        {"text": "\\$3 \\times 10^8\\$ m/s", "is_correct": True},
                        {"text": "\\$3 \\times 10^6\\$ m/s", "is_correct": False},
                    ],
                },
                {
                    "text": "Plain question",
                    "points": 5,
                    "answers": [
                        {"text": "Yes", "is_correct": True},
                        {"text": "No", "is_correct": False},
                    ],
                },
            ],
        )
    )
    questions = list(quiz.questions.order_by("order"))
    assert questions[0].math_enabled is True
    assert questions[1].math_enabled is False


@pytest.mark.django_db
def test_create_quiz_defaults_math_enabled_false():
    category = CategoryFactory()
    quiz = create_quiz(**base_payload(category))
    assert quiz.questions.filter(math_enabled=True).count() == 0


@pytest.mark.django_db
def test_public_quiz_ignores_access_code():
    category = CategoryFactory()
    quiz = create_quiz(**base_payload(category, is_public=True, access_code="SHOULD_BE_IGNORED"))
    assert quiz.is_public is True
    assert quiz.access_code == ""


@pytest.mark.django_db
def test_private_quiz_requires_access_code():
    category = CategoryFactory()
    with pytest.raises(QuizValidationError):
        create_quiz(**base_payload(category, is_public=False, access_code=None))
    with pytest.raises(QuizValidationError):
        create_quiz(**base_payload(category, is_public=False, access_code="  "))
    quiz = create_quiz(**base_payload(category, is_public=False, access_code="SECRET"))
    assert quiz.access_code == "SECRET"


@pytest.mark.django_db
def test_question_requires_two_answers():
    category = CategoryFactory()
    with pytest.raises(QuizValidationError):
        create_quiz(
            **base_payload(
                category,
                questions=[{"text": "Q", "points": 1, "answers": [{"text": "A", "is_correct": True}]}],
            )
        )


@pytest.mark.django_db
def test_question_requires_correct_answer():
    category = CategoryFactory()
    with pytest.raises(QuizValidationError):
        create_quiz(
            **base_payload(
                category,
                questions=[
                    {
                        "text": "Q",
                        "points": 1,
                        "answers": [
                            {"text": "A", "is_correct": False},
                            {"text": "B", "is_correct": False},
                        ],
                    }
                ],
            )
        )


@pytest.mark.django_db
def test_create_quiz_persists_time_limit():
    category = CategoryFactory()
    quiz = create_quiz(**base_payload(category, time_limit=45))
    assert quiz.time_limit_minutes == 45


@pytest.mark.django_db
def test_create_quiz_default_no_time_limit():
    category = CategoryFactory()
    quiz = create_quiz(**base_payload(category))
    assert quiz.time_limit_minutes is None


@pytest.mark.parametrize("value", [-1, 0, 181])
@pytest.mark.django_db
def test_create_quiz_rejects_time_limit_out_of_range(value):
    category = CategoryFactory()
    with pytest.raises(QuizValidationError):
        create_quiz(**base_payload(category, time_limit=value))


@pytest.mark.django_db
def test_create_quiz_rejects_non_numeric_time_limit():
    category = CategoryFactory()
    with pytest.raises(QuizValidationError):
        create_quiz(**base_payload(category, time_limit="abc"))


@pytest.mark.django_db
def test_quiz_requires_title_and_question():
    category = CategoryFactory()
    with pytest.raises(QuizValidationError):
        create_quiz(**base_payload(category, title=""))
    with pytest.raises(QuizValidationError):
        create_quiz(**base_payload(category, questions=[]))


@pytest.mark.django_db
def test_quiz_limited_to_max_questions():
    category = CategoryFactory()
    too_many = [
        {"text": f"Q{i}", "points": 1, "answers": [{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}]}
        for i in range(settings.MAX_QUESTIONS_PER_QUIZ + 1)
    ]
    with pytest.raises(QuizValidationError):
        create_quiz(**base_payload(category, questions=too_many))
