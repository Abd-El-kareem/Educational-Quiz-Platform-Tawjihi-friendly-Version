"""Session-backed quiz state.

Thin, well-defined facade over ``request.session`` so views and services never
touch raw session keys. Guest answers/locks live here; access-code grants use
the same store for both anonymous and authenticated users.
"""

from django.utils import timezone

_ANSWERS_KEY = "quiz_answers_{quiz_id}"
_LOCKED_KEY = "quiz_locked_{quiz_id}"
_ACCESS_KEY = "quiz_access_{quiz_id}"
_STARTED_KEY = "quiz_started_{quiz_id}"


class QuizSessionStore:
    def __init__(self, request):
        self.request = request
        self._session = request.session

    def _answers_key(self, quiz_id):
        return _ANSWERS_KEY.format(quiz_id=quiz_id)

    def _locked_key(self, quiz_id):
        return _LOCKED_KEY.format(quiz_id=quiz_id)

    def _access_key(self, quiz_id):
        return _ACCESS_KEY.format(quiz_id=quiz_id)

    def _started_key(self, quiz_id):
        return _STARTED_KEY.format(quiz_id=quiz_id)

    def _mark_modified(self):
        if hasattr(self._session, "modified"):
            self._session.modified = True

    # --- guest answer persistence -------------------------------------
    def get_answer(self, quiz_id, question_id):
        return self._session.get(self._answers_key(quiz_id), {}).get(str(question_id))

    def get_answers(self, quiz_id):
        return dict(self._session.get(self._answers_key(quiz_id), {}))

    def set_answer(self, quiz_id, question_id, answer_id):
        key = self._answers_key(quiz_id)
        answers = self._session.get(key, {})
        answers[str(question_id)] = str(answer_id)
        self._session[key] = answers
        self._mark_modified()

    def clear_answers(self, quiz_id):
        key = self._answers_key(quiz_id)
        if key in self._session:
            del self._session[key]
            self._mark_modified()

    # --- guest lock ----------------------------------------------------
    def is_locked(self, quiz_id):
        return self._locked_key(quiz_id) in self._session

    def lock(self, quiz_id, earned, total):
        self._session[self._locked_key(quiz_id)] = {"earned": int(earned), "total": int(total)}
        self._mark_modified()

    def get_lock(self, quiz_id):
        return self._session.get(self._locked_key(quiz_id))

    # --- in-progress attempt marker ------------------------------------
    def mark_started(self, quiz_id):
        self._session[self._started_key(quiz_id)] = timezone.now().isoformat()
        self._mark_modified()

    def started_at(self, quiz_id):
        """Return the attempt start datetime, or None if not started/reliable."""
        value = self._session.get(self._started_key(quiz_id))
        if not isinstance(value, str):
            return None
        try:
            return timezone.datetime.fromisoformat(value)
        except ValueError:
            return None

    def clear_started(self, quiz_id):
        if self._started_key(quiz_id) in self._session:
            del self._session[self._started_key(quiz_id)]
            self._mark_modified()

    def has_started(self, quiz_id):
        return bool(self._session.get(self._started_key(quiz_id), False))

    # --- private quiz access (all users) ------------------------------
    def grant_access(self, quiz_id):
        self._session[self._access_key(quiz_id)] = True
        self._mark_modified()

    def has_access(self, quiz_id):
        return self._session.get(self._access_key(quiz_id), False)
