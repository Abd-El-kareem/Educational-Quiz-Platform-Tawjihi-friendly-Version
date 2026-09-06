from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("catalog.urls")),
    path("", include("quizzes.urls")),
    path("", include("scoring.urls")),
    path("api/", include("scoring.api_urls")),
    path("api/", include("ai_feedback.urls")),
]
