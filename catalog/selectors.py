"""Read-only query helpers for the catalog domain."""

from django.db import models

from catalog.models import Category
from quizzes.models import Quiz


def all_categories():
    return Category.objects.all().annotate(quiz_count=models.Count("quizzes"))


def quizzes_in_category(category):
    return Quiz.objects.filter(category=category).select_related("category").annotate(
        question_count=models.Count("questions")
    )
