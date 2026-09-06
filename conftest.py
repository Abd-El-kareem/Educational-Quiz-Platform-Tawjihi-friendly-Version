import pytest

from quizzes.tests.factories import UserFactory, make_quiz


@pytest.fixture
def user_factory(db):
    return UserFactory


@pytest.fixture
def quiz_builder(db):
    return make_quiz


@pytest.fixture
def takeable_quiz(db):
    return make_quiz(
        question_specs=[
            ("Q1", 10, [("A1", True), ("A2", False)]),
            ("Q2", 5, [("B1", False), ("B2", True)]),
        ]
    )
