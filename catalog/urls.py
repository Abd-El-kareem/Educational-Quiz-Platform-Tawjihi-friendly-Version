from django.urls import path

from catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("categories/<int:pk>/", views.CategoryDetailView.as_view(), name="category_detail"),
]
