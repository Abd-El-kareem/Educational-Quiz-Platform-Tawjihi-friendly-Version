from django.conf import settings
from django.db import models


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(
        "catalog.Category", on_delete=models.CASCADE, related_name="quizzes"
    )
    is_public = models.BooleanField(default=True)
    access_code = models.CharField(max_length=32, blank=True, default="")
    time_limit_minutes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Optional time limit in whole minutes (1-180) for taking the quiz.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()
    points = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to="question_images/", blank=True, null=True)
    math_enabled = models.BooleanField(
        default=False,
        help_text="Render the question and its answers as LaTeX (via KaTeX).",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]
