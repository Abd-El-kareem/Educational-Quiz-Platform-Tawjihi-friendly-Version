from django.urls import path

from scoring import api

app_name = "scoring_api"

urlpatterns = [
    path("quizzes/<int:quiz_id>/answers/", api.SaveAnswerView.as_view(), name="save_answer"),
    path("quizzes/<int:quiz_id>/submit/", api.SubmitQuizView.as_view(), name="submit_quiz"),
]
