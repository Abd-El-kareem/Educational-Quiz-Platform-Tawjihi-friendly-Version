import json

import pytest
from django.template import Context, Template
from django.urls import reverse
from django.utils import translation
from django.utils.safestring import SafeData, mark_safe

from core.translations import get_translations_json, t


def test_t_english_identity():
    assert t("Submit") == "Submit"


def test_t_arabic_translates():
    assert t("Submit", lang="ar") == "إرسال"


def test_t_with_kwargs():
    assert t("Total: {total} points", lang="ar", total=5) == "المجموع: 5 نقطة"


def test_t_missing_key_falls_back_to_source():
    assert t("Some string with no translation", lang="ar") == "Some string with no translation"


def test_get_translations_json_arabic():
    data = json.loads(get_translations_json("ar"))
    assert data["Submit"] == "إرسال"


def test_get_translations_json_english_empty():
    assert json.loads(get_translations_json("en")) == {}


def test_tr_tag_renders_arabic():
    with translation.override("ar"):
        out = Template("{% load i18n_tags %}{% tr 'Submit' %}").render(Context({}))
    assert out == "إرسال"


def test_trf_tag_renders_arabic_with_interpolation():
    with translation.override("ar"):
        out = Template(
            "{% load i18n_tags %}{% trf 'Total: {total} points' total=5 %}"
        ).render(Context({}))
    assert out == "المجموع: 5 نقطة"


def test_trf_preserves_safe_html_value_in_arabic():
    # Without this, str.format() downgrades the SafeString from |rich and the
    # template auto-escape re-escapes it, showing raw <img> text on review.
    with translation.override("ar"):
        out = Template(
            "{% load i18n_tags %}"
            "{% trf 'Your answer: {value}' value=html %}"
        ).render(Context({"html": mark_safe('<img src="https://khatt.org/api?c=X">')}))
    assert 'إجابتك: <img src="https://khatt.org/api?c=X">' in out
    assert "&lt;img" not in out


def test_trf_preserves_safe_html_value_in_english():
    with translation.override("en"):
        out = Template(
            "{% load i18n_tags %}"
            "{% trf 'Your answer: {value}' value=html %}"
        ).render(Context({"html": mark_safe('<img src="https://khatt.org/api?c=X">')}))
    assert 'Your answer: <img src="https://khatt.org/api?c=X">' in out
    assert "&lt;img" not in out


def test_t_preserves_safe_value():
    out = t("Your answer: {value}", lang="ar",
            value=mark_safe('<img src="https://khatt.org/api?c=X">'))
    assert isinstance(out, SafeData)
    assert '<img src="https://khatt.org/api?c=X">' in str(out)


def test_t_plain_value_stays_escaped():
    out = t("Your answer: {value}", lang="en", value="a < b")
    assert not isinstance(out, SafeData)
    assert out == "Your answer: a < b"


@pytest.mark.django_db
def test_language_switch_to_arabic_sets_rtl_and_injects_l10n(client):
    client.post(reverse("quizzes:set_language"), {"language": "ar", "next": "/"})
    response = client.get(reverse("catalog:home"))
    assert response.status_code == 200
    assert b'lang="ar"' in response.content
    assert b'dir="rtl"' in response.content
    assert b'window.QUIZ_LANG = "ar"' in response.content
    # The Arabic translation blob must be embedded for the JS layer.
    assert b"window.QUIZ_L10N = {" in response.content


@pytest.mark.django_db
def test_default_language_is_english(client):
    response = client.get(reverse("catalog:home"))
    assert b'lang="en"' in response.content
    assert b'dir="ltr"' in response.content
    assert b"window.QUIZ_L10N = {}" in response.content


@pytest.mark.django_db
def test_arabic_template_renders_translated_literals(client):
    client.post(reverse("quizzes:set_language"), {"language": "ar", "next": "/"})
    response = client.get(reverse("catalog:home"))
    # The navbar brand / platform title is translated only in nav links; verify
    # the language context made the JSON blob carry Arabic strings.
    assert "إرسال".encode("utf-8") in response.content


def test_catalog_plural_words_translate_to_arabic():
    assert t("quiz", lang="ar") == "اختبار"
    assert t("quizzes", lang="ar") == "اختبارات"
    assert t("question", lang="ar") == "سؤال"
    assert t("s", lang="ar") == ""


def test_catalog_plural_english_stays_correct():
    assert t("quizzes", lang="en") == "quizzes"
    assert t("question", lang="en") + t("s", lang="en") == "questions"


@pytest.mark.django_db
def test_login_page_translates_heading_button_and_labels(client):
    client.post(reverse("quizzes:set_language"), {"language": "ar", "next": "/"})
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
    assert "تسجيل الدخول".encode("utf-8") in response.content
    assert "اسم المستخدم".encode("utf-8") in response.content
    assert "كلمة المرور".encode("utf-8") in response.content
    assert "ليس لديك حساب؟".encode("utf-8") in response.content


@pytest.mark.django_db
def test_register_page_translates_heading_button_and_labels(client):
    client.post(reverse("quizzes:set_language"), {"language": "ar", "next": "/"})
    response = client.get(reverse("accounts:register"))
    assert response.status_code == 200
    assert "إنشاء حساب".encode("utf-8") in response.content
    assert "اسم المستخدم".encode("utf-8") in response.content
    assert "تأكيد كلمة المرور".encode("utf-8") in response.content
    assert "لديك حساب بالفعل؟".encode("utf-8") in response.content


@pytest.mark.django_db
def test_login_and_register_stay_english_by_default(client):
    response = client.get(reverse("accounts:login"))
    assert "Log in".encode("utf-8") in response.content
    assert "No account?".encode("utf-8") in response.content
    response = client.get(reverse("accounts:register"))
    assert "Create account".encode("utf-8") in response.content
    assert "Already have an account?".encode("utf-8") in response.content
