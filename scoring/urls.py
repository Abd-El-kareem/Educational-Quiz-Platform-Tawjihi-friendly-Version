from django.urls import path

from scoring import api, views

app_name = "scoring"

urlpatterns = [
    path("scores/", views.ScoreListView.as_view(), name="score_list"),
    path("scores/<int:pk>/", views.ScoreDetailView.as_view(), name="score_detail"),
]
