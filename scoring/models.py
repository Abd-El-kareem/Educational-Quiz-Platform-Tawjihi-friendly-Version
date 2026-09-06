from django.conf import settings
from django.db import models


class Score(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_scores"
    )
    quiz = models.ForeignKey("quizzes.Quiz", on_delete=models.CASCADE, related_name="scores")
    earned = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    attempt_number = models.PositiveSmallIntegerField(default=1)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "quiz", "attempt_number"],
                name="unique_attempt_per_user_quiz",
            )
        ]

    def __str__(self):
        return f"{self.user} on {self.quiz} (attempt {self.attempt_number}): {self.earned}/{self.total}"


class ScoreAnswer(models.Model):
    """Snapshot of one question/answer pair inside a graded attempt.

    ``question_text``/``answer_text`` are stored at submission time so review
    history stays accurate even if the quiz content is edited later.
    """

    score = models.ForeignKey(
        Score, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        "quizzes.Question", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    answer = models.ForeignKey(
        "quizzes.Answer", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    question_text = models.TextField(blank=True, default="")
    answer_text = models.CharField(max_length=1000, blank=True, default="")
    correct_answer_text = models.CharField(max_length=1000, blank=True, default="")
    points = models.PositiveIntegerField(default=0)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["score", "question"], name="unique_score_answer_per_question"
            )
        ]

    def __str__(self):
        return f"score {self.score_id} q{self.question_id}: {self.answer_text}"


class SelectedAnswer(models.Model):
    """In-progress answer selection for an authenticated user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="selected_answers"
    )
    quiz = models.ForeignKey("quizzes.Quiz", on_delete=models.CASCADE, related_name="selected_answers")
    question = models.ForeignKey("quizzes.Question", on_delete=models.CASCADE)
    answer = models.ForeignKey("quizzes.Answer", on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "quiz", "question"], name="unique_selection_per_user_quiz_question"
            )
        ]

    def __str__(self):
        return f"{self.user} #{self.quiz_id} q{self.question_id} -> a{self.answer_id}"
