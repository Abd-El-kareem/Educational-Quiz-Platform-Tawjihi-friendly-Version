from django.contrib import admin

from quizzes.models import Answer, Question, Quiz


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_public", "access_code", "created_by", "created_at")
    list_filter = ("is_public", "category")
    search_fields = ("title",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "points", "math_enabled", "order")
    list_filter = ("quiz", "math_enabled")
    search_fields = ("text",)
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "is_correct", "question")
    list_filter = ("is_correct", "question__quiz")
    search_fields = ("text",)
