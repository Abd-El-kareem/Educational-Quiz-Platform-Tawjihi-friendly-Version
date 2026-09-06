import pytest
from django.urls import reverse

from quizzes.tests.factories import QuizFactory


@pytest.mark.django_db
def test_home_lists_categories(client, category):
    response = client.get(reverse("catalog:home"))
    assert response.status_code == 200
    assert category.name.encode() in response.content


@pytest.mark.django_db
def test_category_detail_lists_quizzes(client, category):
    quiz = QuizFactory(category=category, title="Unique Title")
    response = client.get(reverse("catalog:category_detail", args=[category.pk]))
    assert response.status_code == 200
    assert b"Unique Title" in response.content


@pytest.mark.django_db
def test_category_detail_does_not_list_other_category(client, category):
    other = QuizFactory(title="Other Quiz")
    response = client.get(reverse("catalog:category_detail", args=[category.pk]))
    assert b"Other Quiz" not in response.content
