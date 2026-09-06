from django.urls import path
from django.views.i18n import set_language
from quizzes import views

app_name = "quizzes"

urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
    path("quizzes/new/", views.QuizCreateView.as_view(), name="quiz_create"),
    path("quizzes/<int:pk>/access/", views.QuizAccessView.as_view(), name="quiz_access"),
    path("quizzes/<int:pk>/restart/", views.QuizRestartView.as_view(), name="quiz_restart"),
    path("quizzes/<int:pk>/download/", views.QuizDownloadView.as_view(), name="quiz_download"),
    path("quizzes/<int:pk>/", views.QuizTakeView.as_view(), name="quiz_take"),
]
