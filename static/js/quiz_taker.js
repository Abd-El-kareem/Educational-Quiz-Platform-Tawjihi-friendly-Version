(function () {
  const widget = document.getElementById("quiz-widget");
  if (!widget) return;

  const quizId = widget.dataset.quizId;
  const answersUrl = widget.dataset.answersUrl;
  const submitUrl = widget.dataset.submitUrl;
  const panels = Array.from(document.querySelectorAll(".question-panel"));
  const counter = document.getElementById("question-counter");
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");
  const btnSubmit = document.getElementById("btn-submit");
  const alertBox = document.getElementById("unanswered-alert");
  const unansweredList = document.getElementById("unanswered-list");
  const timerBadge = document.getElementById("timer-badge");
  const timerCount = document.getElementById("timer-count");

  const timeLimit = Math.max(0, parseInt(widget.dataset.timeLimit || "0", 10) || 0);
  const parsedRemaining = parseInt(widget.dataset.remaining || "", 10);
  const initialRemaining =
    Math.max(0, isFinite(parsedRemaining) ? parsedRemaining : timeLimit * 60);
  const endTime = Date.now() + initialRemaining * 1000;
  const WARN_THRESHOLD_SECONDS = 30;
  const TICK_MS = 250;

  let index = 0;
  let submitting = false;
  let timerHandle = null;

  const answered = new Set();
  panels.forEach((panel) => {
    if (panel.querySelector(".answer-radio:checked")) {
      answered.add(panel.dataset.questionId);
    }
  });

  function show(i) {
    index = i;
    panels.forEach((p, idx) => {
      p.style.display = idx === index ? "" : "none";
    });
    counter.textContent = index + 1 + " / " + panels.length;
    btnPrev.disabled = index === 0;
    btnNext.disabled = index === panels.length - 1;
  }

  function savedHint(panel) {
    const hint = panel.querySelector(".saved-hint");
    hint.classList.remove("d-none");
    setTimeout(() => hint.classList.add("d-none"), 1500);
  }

  function csrfToken() {
    const name = "csrftoken=";
    const decoded = decodeURIComponent(document.cookie);
    for (const cookie of decoded.split(";")) {
      let c = cookie.trim();
      if (c.indexOf(name) === 0) return c.substring(name.length);
    }
    return "";
  }

  function pad(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function remainingNow() {
    return Math.max(0, Math.ceil((endTime - Date.now()) / 1000));
  }

  function renderTimer(seconds) {
    if (!timerCount) return;
    timerCount.textContent = pad(Math.floor(seconds / 60)) + ":" + pad(seconds % 60);
    if (timerBadge && seconds <= WARN_THRESHOLD_SECONDS) {
      timerBadge.classList.remove("bg-secondary");
      timerBadge.classList.add("bg-danger");
    }
  }

  document.querySelectorAll(".answer-radio").forEach((radio) => {
    radio.addEventListener("change", () => {
      const panel = radio.closest(".question-panel");
      const qid = radio.dataset.questionId;
      const aid = radio.dataset.answerId;
      panel.classList.remove("border-danger", "border-2");
      fetch(answersUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({ question_id: qid, answer_id: aid }),
      })
        .then((res) => {
          if (res.status === 410) {
            handleTimeout();
            return null;
          }
          if (!res.ok) throw new Error("save failed");
          answered.add(qid);
          savedHint(panel);
        })
        .catch(() => {
          if (submitting) return;
          panel.classList.add("border-danger", "border-2");
          radio.checked = false;
          answered.delete(qid);
        });
    });
  });

  btnPrev.addEventListener("click", () => show(index - 1));
  btnNext.addEventListener("click", () => show(index + 1));
  btnSubmit.addEventListener("click", () => submitNow(false));

  function submitNow(timedOut) {
    if (submitting) return;
    const missing = panels.filter((p) => !answered.has(p.dataset.questionId));
    if (!timedOut && missing.length > 0) {
      unansweredList.textContent = missing
        .map((p) => "#" + (panels.indexOf(p) + 1))
        .join(", ");
      alertBox.classList.remove("d-none");
      missing.forEach((p) => p.classList.add("border-danger", "border-2"));
      show(panels.indexOf(missing[0]));
      return;
    }

    submitting = true;
    if (timerHandle) clearInterval(timerHandle);
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> ' + Q("Submitting…");

    fetch(submitUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ timed_out: !!timedOut }),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((err) => Promise.reject(err));
        }
        return res.json();
      })
      .then(() => {
        window.location.href = window.location.pathname;
      })
      .catch((err) => {
        if (!timedOut && err.detail) {
          alert(Q("Could not submit: ") + (err.detail || Q("Unexpected error.")));
          submitting = false;
          btnSubmit.disabled = false;
          btnSubmit.innerHTML = '<i class="fa-solid fa-paper-plane me-1"></i> ' + Q("Submit quiz");
        } else {
          window.location.href = window.location.pathname;
        }
      });
  }

  function handleTimeout() {
    if (submitting) return;
    panels.forEach((panel) => {
      panel.querySelectorAll(".answer-radio").forEach((r) => {
        r.disabled = true;
      });
    });
    btnNext.disabled = true;
    btnPrev.disabled = true;
    renderTimer(0);
    submitNow(true);
  }

  function tick() {
    try {
      const left = remainingNow();
      renderTimer(left);
      if (left <= 0) {
        if (timerHandle) clearInterval(timerHandle);
        handleTimeout();
      }
    } catch (e) {
      // Never let a bad tick kill the countdown.
    }
  }

  if (timeLimit > 0) {
    renderTimer(remainingNow());
    if (remainingNow() <= 0) {
      handleTimeout();
    } else {
      timerHandle = setInterval(tick, TICK_MS);
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) return;
        try {
          tick();
        } catch (e) {
          // Ignore; the interval still catches up.
        }
      });
    }
  }

  show(0);
})();