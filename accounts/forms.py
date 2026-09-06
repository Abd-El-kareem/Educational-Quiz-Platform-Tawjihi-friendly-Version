from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import get_language

from core.translations import t


def _localized_label(text):
    return t(text, lang=get_language())


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _localized_label("Username")
        self.fields["password1"].label = _localized_label("Password")
        self.fields["password2"].label = _localized_label("Password confirmation")


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _localized_label("Username")
        self.fields["password"].label = _localized_label("Password")
