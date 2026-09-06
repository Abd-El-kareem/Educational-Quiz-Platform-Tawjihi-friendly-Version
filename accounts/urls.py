from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginRedirectView.as_view(), name="login"),
    path("logout/", views.LogoutRedirectView.as_view(), name="logout"),
]
