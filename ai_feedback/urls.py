from django.urls import path

from ai_feedback import views

app_name = "ai_feedback"

urlpatterns = [
    path("questions/<int:question_id>/ai-explain/", views.QuestionExplainView.as_view(), name="ai_explain"),
]
