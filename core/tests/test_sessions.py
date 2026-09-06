from types import SimpleNamespace

from django.utils import timezone

from core.sessions import QuizSessionStore


class FakeSession(dict):
    modified = False


def make_store():
    return QuizSessionStore(SimpleNamespace(session=FakeSession()))


def test_set_and_get_answer():
    store = make_store()
    store.set_answer(1, 10, 100)
    assert store.get_answer(1, 10) == "100"
    assert store.get_answers(1) == {"10": "100"}
    assert store.get_answer(1, 11) is None


def test_answers_are_per_quiz():
    store = make_store()
    store.set_answer(1, 10, 100)
    store.set_answer(2, 20, 200)
    assert store.get_answers(1) == {"10": "100"}
    assert store.get_answers(2) == {"20": "200"}


def test_clear_answers():
    store = make_store()
    store.set_answer(1, 10, 100)
    store.clear_answers(1)
    assert store.get_answers(1) == {}


def test_lock_flow():
    store = make_store()
    assert not store.is_locked(1)
    store.lock(1, earned=30, total=50)
    assert store.is_locked(1)
    assert store.get_lock(1) == {"earned": 30, "total": 50}


def test_access_flags_are_per_quiz():
    store = make_store()
    assert not store.has_access(1)
    store.grant_access(1)
    assert store.has_access(1)
    assert not store.has_access(2)


def test_started_at_is_none_before_start():
    store = make_store()
    assert not store.has_started(1)
    assert store.started_at(1) is None


def test_mark_started_stores_aware_timestamp():
    store = make_store()
    store.mark_started(1)
    assert store.has_started(1)
    started = store.started_at(1)
    assert started is not None
    assert timezone.is_aware(started)


def test_started_at_returns_none_for_legacy_marker():
    store = make_store()
    store._session["quiz_started_1"] = True
    assert store.has_started(1)
    assert store.started_at(1) is None


def test_clear_started():
    store = make_store()
    store.mark_started(1)
    assert store.has_started(1)
    store.clear_started(1)
    assert not store.has_started(1)
    assert store.started_at(1) is None
