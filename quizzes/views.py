from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import slugify
from django.utils.translation import get_language
from django.views import View
from django.views.generic import DetailView, TemplateView

from core.sessions import QuizSessionStore
from core.translations import t
from quizzes import selectors as quiz_selectors
from quizzes.models import Quiz
from quizzes.offline import render_offline_quiz
from quizzes.services import QuizValidationError, create_quiz
from scoring import selectors as scoring_selectors
from scoring import services as scoring_services
from catalog.models import Category


class QuizTakeView(DetailView):
    template_name = "quizzes/quiz_take.html"
    context_object_name = "quiz"

    def get_object(self, queryset=None):
        quiz = quiz_selectors.quiz_with_questions(self.kwargs["pk"])
        if quiz is None:
            raise Http404
        return quiz

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = QuizSessionStore(self.request)
        quiz = context["quiz"]
        user = self.request.user
        context["total_points"] = quiz_selectors.quiz_total_points(quiz)
        context["needs_access"] = not quiz.is_public and not store.has_access(quiz.id)
        context["has_math"] = any(q.math_enabled for q in quiz.questions.all())

        if user.is_authenticated:
            context["attempts_total"] = scoring_services.MAX_ATTEMPTS
            context["attempts_used"] = scoring_services.attempt_count(
                user=user, quiz_id=quiz.id
            )
            context["attempts_left"] = scoring_services.attempts_left(
                user=user, quiz_id=quiz.id
            )
            context["last_score"] = scoring_selectors.user_score_for_quiz(user, quiz)
            started = store.has_started(quiz.id) and context["attempts_left"] > 0
        else:
            locked = scoring_selectors.user_locked_result(user, store, quiz)
            context["attempts_total"] = 1
            context["attempts_used"] = 1 if locked else 0
            context["attempts_left"] = 0 if locked else 1
            context["last_score"] = locked
            started = False

        context["submitted"] = context["attempts_used"] > 0 and not started
        if not context["submitted"]:
            selected_map = scoring_selectors.selected_map(user, store, quiz)
            context["selected_answers"] = [int(v) for v in selected_map.values()]

        in_progress = not context["submitted"] and not context["needs_access"]
        if in_progress:
            if not store.has_started(quiz.id):
                store.mark_started(quiz.id)
            context["time_limit_minutes"] = quiz.time_limit_minutes
            context["remaining_seconds"] = scoring_services.remaining_seconds(store, quiz)
        else:
            context["time_limit_minutes"] = None
            context["remaining_seconds"] = None
        return context


class QuizRestartView(View):
    """Start a fresh attempt, discarding previous in-progress selections."""

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        store = QuizSessionStore(request)
        if not quiz.is_public and not store.has_access(quiz.id):
            messages.error(
                request, t("This private quiz requires a valid access code.", lang=get_language())
            )
            return redirect("quizzes:quiz_take", pk=quiz.id)
        try:
            scoring_services.start_attempt(
                user=request.user, store=store, quiz_id=quiz.id
            )
        except scoring_services.QuizNotFoundError:
            raise Http404
        return redirect("quizzes:quiz_take", pk=quiz.id)


class QuizAccessView(View):
    """Verify the access code for a private quiz and grant session access."""

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        store = QuizSessionStore(request)
        code = request.POST.get("access_code", "").strip()
        if code and quiz.access_code == code:
            store.grant_access(quiz.id)
            return redirect("quizzes:quiz_take", pk=quiz.id)
        messages.error(request, t("Incorrect access code. Try again.", lang=get_language()))
        return redirect("quizzes:quiz_take", pk=quiz.id)


class QuizDownloadView(LoginRequiredMixin, View):
    """Serve the quiz as a single self-contained, offline-runnable HTML file.

    Only registered users may download; private quizzes additionally require
    the session access grant, matching the take-page gate.
    """

    def get(self, request, pk):
        quiz = quiz_selectors.quiz_with_questions(pk)
        if quiz is None:
            raise Http404
        store = QuizSessionStore(request)
        if not quiz.is_public and not store.has_access(quiz.id):
            messages.error(
                request,
                t("This private quiz requires a valid access code.", lang=get_language()),
            )
            return redirect("quizzes:quiz_take", pk=quiz.id)
        html = render_offline_quiz(quiz, lang=get_language())
        filename = f"{slugify(quiz.title) or 'quiz'}-quiz.html"
        response = HttpResponse(html, content_type="text/html; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class QuizCreateView(LoginRequiredMixin, TemplateView):
    template_name = "quizzes/quiz_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context.setdefault(
            "form_data",
            {"title": "", "category": None, "is_public": True, "access_code": "", "time_limit": ""},
        )
        return context

    def post(self, request):
        parsed, errors = parse_quiz_form(request)
        if errors:
            return self.render_to_response(
                self.get_context_data(errors=errors, form_data=parsed)
            )
        try:
            quiz = create_quiz(
                created_by=request.user,
                title=parsed["title"],
                category=parsed["category"],
                is_public=parsed["is_public"],
                access_code=parsed["access_code"],
                time_limit=parsed["time_limit"],
                questions=parsed["questions"],
                lang=get_language(),
            )
        except QuizValidationError as exc:
            return self.render_to_response(
                self.get_context_data(errors=[str(exc)], form_data=parsed)
            )
        return redirect("quizzes:quiz_take", pk=quiz.id)


def parse_quiz_form(request):
    """Turn the dynamic question/answer form POST into validated structures.

    Field names: ``questions-<i>-text|points|image|math`` and
    ``questions-<i>-answers-<j>-text|correct``.
    """
    post = request.POST
    files = request.FILES
    lang = get_language()
    title = (post.get("title") or "").strip()
    category = Category.objects.filter(pk=post.get("category")).first()
    errors = []

    time_limit = None
    if post.get("time_limit"):
        try:
            time_limit = int(post.get("time_limit"))
        except (TypeError, ValueError):
            errors.append(t("Time limit must be a whole number of minutes.", lang))

    index = 0
    questions = []
    if not title:
        errors.append(t("Quiz title is required.", lang))
    if category is None:
        errors.append(t("Please choose a category.", lang))

    while post.get(f"questions-{index}-text") is not None:
        answers = []
        a_index = 0
        while post.get(f"questions-{index}-answers-{a_index}-text") is not None:
            answers.append(
                {
                    "text": post.get(f"questions-{index}-answers-{a_index}-text"),
                    "is_correct": post.get(f"questions-{index}-answers-{a_index}-correct")
                    == "on",
                }
            )
            a_index += 1
        questions.append(
            {
                "text": post.get(f"questions-{index}-text"),
                "points": post.get(f"questions-{index}-points") or 1,
                "image": files.get(f"questions-{index}-image"),
                "math_enabled": post.get(f"questions-{index}-math") == "on",
                "answers": answers,
            }
        )
        index += 1

    return (
        {
            "title": title,
            "category": category,
            "is_public": post.get("is_public") == "on",
            "access_code": post.get("access_code"),
            "time_limit": time_limit,
            "questions": questions,
        },
        errors,
    )
