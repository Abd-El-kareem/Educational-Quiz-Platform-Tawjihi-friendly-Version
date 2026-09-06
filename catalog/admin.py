from django.contrib import admin

from catalog.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "quiz_count")
    search_fields = ("name",)

    @admin.display(description="Quizzes")
    def quiz_count(self, obj):
        return obj.quizzes.count()
