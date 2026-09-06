import factory

from scoring.models import Score, SelectedAnswer
from quizzes.tests.factories import AnswerFactory, QuestionFactory, QuizFactory, UserFactory


class ScoreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Score

    user = factory.SubFactory(UserFactory)
    quiz = factory.SubFactory(QuizFactory)
    earned = 0
    total = 10


class SelectedAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SelectedAnswer

    user = factory.SubFactory(UserFactory)
    quiz = factory.SubFactory(QuizFactory)
    question = factory.SubFactory(QuestionFactory)
    answer = factory.SubFactory(AnswerFactory)
