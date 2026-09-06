from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.views.generic import FormView

from accounts.forms import LoginForm, RegisterForm


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = RegisterForm
    success_url = "/"

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.get_success_url())


class LoginRedirectView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm


class LogoutRedirectView(LogoutView):
    pass
