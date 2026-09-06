import pytest

from quizzes.tests.factories import CategoryFactory, QuizFactory


@pytest.fixture
def category(db):
    return CategoryFactory()


@pytest.fixture
def quiz(db):
    return QuizFactory()
