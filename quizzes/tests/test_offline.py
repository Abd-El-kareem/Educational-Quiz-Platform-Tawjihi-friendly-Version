import base64

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from quizzes.offline import _embed_khatt, render_offline_quiz
from quizzes.tests.factories import UserFactory, make_quiz

KHATT_IMG = (
    '<img src="https://khatt.org/api?c=%D8%B3%20%3D%20%2F%D8%B9%D9%84%D9%89"'
    ' width="100" height="40" alt="س">'
)

FAKE_PNG = b"\x89PNG\r\n\x1a\nfake-khatt-bytes"


@pytest.fixture
def stub_fetches(monkeypatch):
    """Return canned bytes for every remote fetch, never hitting the network."""

    def fetcher(url, timeout=10.0):
        if "khatt.org" in url:
            return FAKE_PNG
        if url.endswith(".woff2"):
            return b"FAKE-WOFF2-FONT"
        if url.endswith("katex.min.css"):
            return (
                b"@font-face{font-family:'KaTeX_Main';src:url(fonts/KaTeX_Main-Regular.woff2)"
                b" format('woff2');}"
            )
        if url.endswith("katex.min.js"):
            return b"/* fake katex */ var katex = {};"
        if "auto-render.min.js" in url:
            return b"/* fake auto-render */ var renderMathInElement = function(){};"
        return b""

    monkeypatch.setattr("quizzes.offline._fetch_bytes", fetcher)
    return fetcher


@pytest.mark.django_db
def test_offline_quiz_is_standalone_html(takeable_quiz, stub_fetches):
    html = render_offline_quiz(takeable_quiz, lang="en")
    assert html.startswith("<!DOCTYPE html>")
    assert "offline_quiz.css" not in html
    assert "offline_quiz.js" not in html
    assert "{{" not in html
    assert "{%" not in html


@pytest.mark.django_db
def test_offline_quiz_embeds_correct_answers_for_local_scoring(takeable_quiz, stub_fetches):
    html = render_offline_quiz(takeable_quiz, lang="en")
    assert html.count('data-correct="1"') == 2
    assert 'id="quiz-results"' in html
    assert 'id="quiz-widget"' in html


@pytest.mark.django_db
def test_offline_quiz_embeds_timer_and_total(takeable_quiz, stub_fetches):
    takeable_quiz.time_limit_minutes = 10
    takeable_quiz.save()
    html = render_offline_quiz(takeable_quiz, lang="en")
    assert 'data-time-limit="10"' in html
    assert 'data-total="15"' in html
    assert 'id="timer-badge"' in html


@pytest.mark.django_db
def test_offline_quiz_omits_timer_without_time_limit(takeable_quiz, stub_fetches):
    html = render_offline_quiz(takeable_quiz, lang="en")
    assert "data-time-limit" not in html
    assert 'id="timer-badge"' not in html


@pytest.mark.django_db
def test_offline_quiz_embeds_khatt_images_as_data_uris(takeable_quiz, stub_fetches):
    takeable_quiz.questions.update(math_enabled=True, text=KHATT_IMG)
    html = render_offline_quiz(takeable_quiz, lang="ar")
    assert "khatt-content" in html
    encoded = base64.b64encode(FAKE_PNG).decode("ascii")
    assert f"data:image/png;base64,{encoded}" in html
    assert "khatt.org/api?c=" not in html


@pytest.mark.django_db
def test_offline_quiz_keeps_src_when_fetch_fails(takeable_quiz, monkeypatch):
    takeable_quiz.questions.update(math_enabled=True, text=KHATT_IMG)
    monkeypatch.setattr("quizzes.offline._fetch_bytes", lambda url, timeout=10.0: None)
    html = render_offline_quiz(takeable_quiz, lang="ar")
    assert "khatt.org/api?c=" in html


@pytest.mark.django_db
def test_offline_quiz_embeds_uploaded_question_image(takeable_quiz, stub_fetches, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path / "media")
    question = takeable_quiz.questions.get(order=0)
    question.image = SimpleUploadedFile(
        "diagram.png", b"\x89PNG\r\n\x1a\nuploaded-image", content_type="image/png"
    )
    question.save()
    html = render_offline_quiz(takeable_quiz, lang="en")
    assert 'alt="Question image"' in html
    assert "data:image/png;base64," in html
    assert "diagram.png" not in html


@pytest.mark.django_db
def test_offline_quiz_includes_katex_for_math_in_english(takeable_quiz, stub_fetches):
    takeable_quiz.questions.update(math_enabled=True, text=r"Solve $x^2$")
    html = render_offline_quiz(takeable_quiz, lang="en")
    assert "fake katex" in html
    assert "auto-render" in html
    assert "quote-question math-content" in html
    assert 'class="khatt-content"' not in html
    assert "data:font/woff2;base64," in html


@pytest.mark.django_db
def test_offline_quiz_omits_katex_in_arabic_khatt_engine(takeable_quiz, stub_fetches):
    takeable_quiz.questions.update(math_enabled=True, text=r"Solve $x^2$")
    html = render_offline_quiz(takeable_quiz, lang="ar")
    assert "fake katex" not in html
    assert "quote-question math-content" not in html


@pytest.mark.django_db
def test_offline_quiz_escapes_plain_question_text(takeable_quiz, stub_fetches):
    takeable_quiz.questions.update(text='10 < 20 & "quoted"')
    html = render_offline_quiz(takeable_quiz, lang="en")
    assert "&lt; 20 &amp; &quot;quoted&quot;" in html
    assert "< 20" not in html


@pytest.mark.django_db
def test_offline_quiz_arabic_uses_rtl_and_translated_labels(takeable_quiz, stub_fetches):
    html = render_offline_quiz(takeable_quiz, lang="ar")
    assert 'dir="rtl"' in html
    assert 'OFFLINE_LANG = "ar"' in html
    assert "إعادة الاختبار" in html


def test_embed_khatt_ignores_non_khatt_images(stub_fetches):
    markup = '<img src="https://example.com/photo.png" alt="x">'
    out = _embed_khatt(markup)
    assert out == markup


# --------------------------------------------------------------------------
# Download view
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_download_requires_login(client, takeable_quiz):
    response = client.get(reverse("quizzes:quiz_download", args=[takeable_quiz.pk]))
    assert response.status_code == 302
    assert "login" in response.url


@pytest.mark.django_db
def test_download_serves_offline_file(client, takeable_quiz, stub_fetches):
    user = UserFactory()
    client.force_login(user)
    response = client.get(reverse("quizzes:quiz_download", args=[takeable_quiz.pk]))
    assert response.status_code == 200
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert response["Content-Disposition"].startswith('attachment; filename="')
    assert response["Content-Disposition"].endswith('-quiz.html"')
    assert response.content.startswith(b"<!DOCTYPE html>")


@pytest.mark.django_db
def test_download_returns_nice_filename(client, takeable_quiz, stub_fetches):
    takeable_quiz.title = "Algebra Basics!"
    takeable_quiz.save()
    user = UserFactory()
    client.force_login(user)
    response = client.get(reverse("quizzes:quiz_download", args=[takeable_quiz.pk]))
    assert 'filename="algebra-basics-quiz.html"' in response["Content-Disposition"]


@pytest.mark.django_db
def test_download_404_for_unknown_quiz(client, stub_fetches):
    user = UserFactory()
    client.force_login(user)
    response = client.get(reverse("quizzes:quiz_download", args=[99999]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_private_quiz_download_redirects_until_access_granted(client, takeable_quiz, stub_fetches):
    takeable_quiz.is_public = False
    takeable_quiz.access_code = "SECRET"
    takeable_quiz.save()
    user = UserFactory()
    client.force_login(user)

    gated = client.get(reverse("quizzes:quiz_download", args=[takeable_quiz.pk]))
    assert gated.status_code == 302
    assert f"/quizzes/{takeable_quiz.pk}/" in gated.url

    client.post(reverse("quizzes:quiz_access", args=[takeable_quiz.pk]), {"access_code": "SECRET"})
    unlocked = client.get(reverse("quizzes:quiz_download", args=[takeable_quiz.pk]))
    assert unlocked.status_code == 200


@pytest.mark.django_db
def test_download_respects_language(client, takeable_quiz, stub_fetches):
    user = UserFactory()
    client.force_login(user)
    response = client.get(
        reverse("quizzes:quiz_download", args=[takeable_quiz.pk]),
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert 'dir="rtl"' in response.content.decode()
    assert 'OFFLINE_LANG = "ar"' in response.content.decode()


# --------------------------------------------------------------------------
# Download buttons
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_take_page_shows_download_button(client, takeable_quiz):
    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert response.status_code == 200
    assert f'/quizzes/{takeable_quiz.pk}/download/'.encode() in response.content
    assert b"Download" in response.content


@pytest.mark.django_db
def test_submitted_card_shows_download_button(client, takeable_quiz):
    user = UserFactory()
    client.force_login(user)
    for question in takeable_quiz.questions.all():
        correct = question.answers.get(is_correct=True)
        client.post(
            reverse("scoring_api:save_answer", args=[takeable_quiz.pk]),
            {"question_id": question.id, "answer_id": correct.id},
            content_type="application/json",
        )
    client.post(reverse("scoring_api:submit_quiz", args=[takeable_quiz.pk]))

    response = client.get(reverse("quizzes:quiz_take", args=[takeable_quiz.pk]))
    assert f'/quizzes/{takeable_quiz.pk}/download/'.encode() in response.content
    assert b"Download quiz (offline)" in response.content


@pytest.mark.django_db
def test_score_list_shows_download_button(client, takeable_quiz, stub_fetches):
    from scoring.tests.factories import ScoreFactory

    user = UserFactory()
    client.force_login(user)
    ScoreFactory(user=user, quiz=takeable_quiz)

    response = client.get(reverse("scoring:score_list"))
    assert response.status_code == 200
    assert f'/quizzes/{takeable_quiz.pk}/download/'.encode() in response.content
    assert b"Download" in response.content


@pytest.mark.django_db
def test_score_detail_shows_download_button(client, takeable_quiz, stub_fetches):
    from scoring.tests.factories import ScoreFactory

    user = UserFactory()
    client.force_login(user)
    score = ScoreFactory(user=user, quiz=takeable_quiz)

    response = client.get(reverse("scoring:score_detail", args=[score.pk]))
    assert response.status_code == 200
    assert f'/quizzes/{takeable_quiz.pk}/download/'.encode() in response.content
    assert b"Download quiz (offline)" in response.content