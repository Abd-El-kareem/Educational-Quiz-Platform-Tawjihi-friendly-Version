from django.contrib import admin

from scoring.models import Score, ScoreAnswer, SelectedAnswer


class ScoreAnswerInline(admin.TabularInline):
    model = ScoreAnswer
    extra = 0
    readonly_fields = (
        "question",
        "answer",
        "question_text",
        "answer_text",
        "correct_answer_text",
        "points",
        "is_correct",
    )
    can_delete = False


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "attempt_number", "earned", "total", "completed_at")
    list_filter = ("quiz", "completed_at")
    search_fields = ("user__username", "quiz__title")
    inlines = [ScoreAnswerInline]


@admin.register(ScoreAnswer)
class ScoreAnswerAdmin(admin.ModelAdmin):
    list_display = ("score", "question", "answer_text", "points", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("answer_text", "question_text")


@admin.register(SelectedAnswer)
class SelectedAnswerAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "question", "answer", "updated_at")
    search_fields = ("user__username",)
