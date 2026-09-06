from django.utils.translation import get_language
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.sessions import QuizSessionStore
from core.translations import t
from scoring import services
from scoring.serializers import SaveAnswerSerializer, SubmitResultSerializer


class SaveAnswerView(APIView):
    serializer_class = SaveAnswerSerializer

    def post(self, request, quiz_id):
        serializer = SaveAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.record_answer(
                user=request.user,
                store=QuizSessionStore(request),
                quiz_id=quiz_id,
                question_id=serializer.validated_data["question_id"],
                answer_id=serializer.validated_data["answer_id"],
            )
        except services.QuizNotFoundError:
            return Response({"detail": t("Quiz not found.", lang=get_language())}, status=status.HTTP_404_NOT_FOUND)
        except services.AccessDeniedError:
            return Response(
                {"detail": t("Access code required.", lang=get_language())}, status=status.HTTP_403_FORBIDDEN
            )
        except services.AlreadySubmittedError:
            return Response(
                {"detail": t("Already submitted.", lang=get_language())}, status=status.HTTP_409_CONFLICT
            )
        except services.TimeExpiredError:
            return Response(
                {"detail": t("Time's up! Your answers were submitted.", lang=get_language())},
                status=status.HTTP_410_GONE,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "ok"})


class SubmitQuizView(APIView):
    serializer_class = SubmitResultSerializer

    def post(self, request, quiz_id):
        try:
            result = services.submit_quiz(
                user=request.user,
                store=QuizSessionStore(request),
                quiz_id=quiz_id,
                timed_out=bool(request.data.get("timed_out")),
            )
        except services.QuizNotFoundError:
            return Response({"detail": t("Quiz not found.", lang=get_language())}, status=status.HTTP_404_NOT_FOUND)
        except services.AccessDeniedError:
            return Response(
                {"detail": t("Access code required.", lang=get_language())}, status=status.HTTP_403_FORBIDDEN
            )
        except services.AlreadySubmittedError:
            return Response(
                {"detail": t("Already submitted.", lang=get_language())}, status=status.HTTP_409_CONFLICT
            )
        except services.UnansweredQuestionsError as exc:
            return Response(
                {
                    "detail": t("Not all questions are answered.", lang=get_language()),
                    "unanswered": exc.unanswered_question_ids,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SubmitResultSerializer(result)
        return Response(serializer.data)
