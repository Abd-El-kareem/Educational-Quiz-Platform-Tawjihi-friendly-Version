from django.views.generic import DetailView, ListView

from catalog import selectors
from catalog.models import Category


class HomeView(ListView):
    template_name = "catalog/home.html"
    context_object_name = "categories"

    def get_queryset(self):
        return selectors.all_categories()


class CategoryDetailView(DetailView):
    template_name = "catalog/category_detail.html"
    model = Category
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["quizzes"] = selectors.quizzes_in_category(self.object)
        return context
