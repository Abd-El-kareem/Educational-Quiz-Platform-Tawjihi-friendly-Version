from django.http import Http404
from django.utils.translation import get_language
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_feedback import services
from ai_feedback.serializers import ExplainSerializer
from quizzes import selectors as quiz_selectors
from quizzes.models import Answer


class QuestionExplainView(APIView):
    serializer_class = ExplainSerializer

    def post(self, request, question_id):
        question = quiz_selectors.get_question_or_none(question_id)
        if question is None:
            raise Http404("Question not found.")

        selected_answer = None
        score_id = request.data.get("score_id")
        if score_id is not None:
            from scoring.models import Score

            score = Score.objects.filter(pk=score_id, user=request.user).first()
            if score is None:
                raise Http404("Score not found.")
            score_answer = score.answers.filter(question_id=question.id).first()
            if score_answer is not None and score_answer.answer_id:
                selected_answer = Answer.objects.filter(
                    pk=score_answer.answer_id
                ).first()
        elif request.user.is_authenticated:
            from scoring.models import SelectedAnswer

            selection = (
                SelectedAnswer.objects.filter(
                    user=request.user, question=question
                ).first()
            )
            if selection:
                selected_answer = Answer.objects.filter(pk=selection.answer_id).first()
        else:
            from core.sessions import QuizSessionStore

            store = QuizSessionStore(request)
            answer_id = store.get_answer(question.quiz_id, question.id)
            if answer_id:
                selected_answer = Answer.objects.filter(pk=answer_id).first()

        try:
            html = services.ask_for_explanation(question, selected_answer, lang=get_language())
        except services.AiFeedbackError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(ExplainSerializer({"html": html}).data)
