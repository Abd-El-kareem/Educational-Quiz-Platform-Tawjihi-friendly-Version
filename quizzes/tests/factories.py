import factory
from django.contrib.auth.models import User

from catalog.models import Category
from quizzes.models import Answer, Question, Quiz


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted if extracted else "testpass123")
        obj.save()


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")


class QuizFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quiz

    title = factory.Sequence(lambda n: f"Quiz {n}")
    category = factory.SubFactory(CategoryFactory)
    is_public = True
    access_code = ""


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    quiz = factory.SubFactory(QuizFactory)
    text = factory.Sequence(lambda n: f"Question {n}")
    points = 10
    order = factory.Sequence(lambda n: n)


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Answer

    question = factory.SubFactory(QuestionFactory)
    text = factory.Sequence(lambda n: f"Answer {n}")
    is_correct = False
    order = factory.Sequence(lambda n: n)


def make_quiz(question_specs=None, **quiz_kwargs):
    """Build a quiz with questions/answers.

    question_specs: list of (text, points, [(answer_text, is_correct), ...]).
    """
    quiz = QuizFactory(**quiz_kwargs)
    if question_specs is None:
        question_specs = [("Q1", 10, [("A1", True), ("A2", False)])]
    for order, (text, points, answers) in enumerate(question_specs):
        question = QuestionFactory(quiz=quiz, text=text, points=points, order=order)
        for a_order, (answer_text, is_correct) in enumerate(answers):
            AnswerFactory(
                question=question,
                text=answer_text,
                is_correct=is_correct,
                order=a_order,
            )
    return quiz
