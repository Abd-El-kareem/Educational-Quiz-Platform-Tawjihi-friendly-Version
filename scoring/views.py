from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from scoring import selectors
from scoring.models import Score, ScoreAnswer


@method_decorator(login_required, name="dispatch")
class ScoreListView(ListView):
    template_name = "scoring/score_list.html"
    context_object_name = "scores"

    def get_queryset(self):
        return selectors.user_scores(self.request.user)


@method_decorator(login_required, name="dispatch")
class ScoreDetailView(DetailView):
    """Review page for a single graded attempt, including per-question answers."""

    template_name = "scoring/score_detail.html"
    context_object_name = "score"

    def get_queryset(self):
        return (
            Score.objects.filter(user=self.request.user)
            .select_related("quiz", "quiz__category")
            .prefetch_related(
                Prefetch("answers", queryset=ScoreAnswer.objects.select_related("question"))
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_math"] = any(
            q.math_enabled for q in self.object.quiz.questions.all()
        )
        return context
