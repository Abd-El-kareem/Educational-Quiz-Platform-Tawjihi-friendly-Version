(function () {
  "use strict";

  // KaTeX auto-render for math questions (safe no-op when kaTeX is absent).
  if (typeof renderMathInElement !== "undefined") {
    var opts = {
      throwOnError: false,
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "\\(", right: "\\)", display: false },
        { left: "\\[", right: "\\]", display: true },
        { left: "$", right: "$", display: false },
      ],
    };
    document.querySelectorAll(".math-content").forEach(function (el) {
      renderMathInElement(el, opts);
    });
  }

  function Q(key) {
    if (
      window.OFFLINE_LANG === "ar" &&
      window.OFFLINE_I18N &&
      window.OFFLINE_I18N[key] != null
    ) {
      return window.OFFLINE_I18N[key];
    }
    return key;
  }

  function Qf(key, map) {
    var s = Q(key);
    for (var k in map) {
      s = s.split("{" + k + "}").join(String(map[k]));
    }
    return s;
  }

  var widget = document.getElementById("quiz-widget");
  if (!widget) return;

  var quizId = widget.dataset.quizId;
  var timeLimit = Math.max(0, parseInt(widget.dataset.timeLimit || "0", 10) || 0);
  var totalPoints = Math.max(0, parseInt(widget.dataset.total || "0", 10) || 0);
  var STORAGE_KEY = "offline_quiz_" + quizId;
  var WARN_SECONDS = 30;
  var TICK_MS = 250;

  var zone = document.getElementById("quiz-zone");
  var results = document.getElementById("quiz-results");
  var resultsSummary = document.getElementById("results-summary");
  var resultsNote = document.getElementById("results-note");
  var resultsCorrect = document.getElementById("results-correct");
  var resultsBody = document.getElementById("results-body");
  var btnRetake = document.getElementById("btn-retake");
  var panels = Array.from(document.querySelectorAll(".question-panel"));
  var radios = Array.from(document.querySelectorAll(".answer-radio"));
  var counter = document.getElementById("question-counter");
  var btnPrev = document.getElementById("btn-prev");
  var btnNext = document.getElementById("btn-next");
  var btnSubmit = document.getElementById("btn-submit");
  var alertBox = document.getElementById("unanswered-alert");
  var unansweredList = document.getElementById("unanswered-list");
  var timerBadge = document.getElementById("timer-badge");
  var timerCount = document.getElementById("timer-count");

  function readStorage() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    } catch (e) {
      return null;
    }
  }

  function writeStorage(obj) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(obj));
    } catch (e) {
      // private mode / unsupported storage: state still works in-memory
    }
  }

  function clearStorage() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      /* ignore */
    }
  }

  var saved = readStorage();
  var answers = (saved && saved.answers) || {};
  var endTime = saved && typeof saved.endTime === "number" ? saved.endTime : null;
  var done = !!(saved && saved.done);

  var answered = new Set(Object.keys(answers));

  radios.forEach(function (r) {
    if (answers[r.dataset.questionId] === r.dataset.answerId) {
      r.checked = true;
    }
    r.addEventListener("change", function () {
      var panel = r.closest(".question-panel");
      panel.classList.remove("is-unanswered");
      var qid = r.dataset.questionId;
      var aid = r.dataset.answerId;
      answers[qid] = aid;
      answered.add(qid);
      writeStorage({ answers: answers, endTime: endTime, done: done });
      savedHint(panel);
    });
  });

  var index = 0;
  var submitting = false;
  var timerHandle = null;

  function show(i) {
    index = i;
    panels.forEach(function (p, idx) {
      p.style.display = idx === index ? "" : "none";
    });
    counter.textContent = index + 1 + " / " + panels.length;
    btnPrev.disabled = index === 0;
    btnNext.disabled = index === panels.length - 1;
  }

  function savedHint(panel) {
    var hint = panel.querySelector(".saved-hint");
    if (!hint) return;
    hint.classList.remove("d-none");
    clearTimeout(hint._t);
    hint._t = setTimeout(function () {
      hint.classList.add("d-none");
    }, 1500);
  }

  function pad(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function remainingNow() {
    if (typeof endTime !== "number") return timeLimit * 60;
    return Math.max(0, Math.ceil((endTime - Date.now()) / 1000));
  }

  function renderTimer(seconds) {
    if (!timerCount) return;
    timerCount.textContent = pad(Math.floor(seconds / 60)) + ":" + pad(seconds % 60);
    if (timerBadge && seconds <= WARN_SECONDS) {
      timerBadge.classList.remove("chip-time");
      timerBadge.classList.add("bg-danger");
    }
  }

  function startTimer() {
    if (timeLimit <= 0) return;
    if (typeof endTime !== "number" || endTime <= 0) {
      endTime = Date.now() + timeLimit * 60000;
      writeStorage({ answers: answers, endTime: endTime, done: done });
    }
    if (remainingNow() <= 0) {
      handleTimeout();
      return;
    }
    timerHandle = setInterval(tick, TICK_MS);
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) tick();
    });
  }

  function tick() {
    var left = remainingNow();
    renderTimer(left);
    if (left <= 0) {
      if (timerHandle) clearInterval(timerHandle);
      handleTimeout();
    }
  }

  function handleTimeout() {
    if (submitting) return;
    panels.forEach(function (panel) {
      panel.querySelectorAll(".answer-radio").forEach(function (r) {
        r.disabled = true;
      });
    });
    btnNext.disabled = true;
    btnPrev.disabled = true;
    renderTimer(0);
    submitNow(true);
  }

  function optionText(radio) {
    if (!radio) return null;
    var opt = radio.closest(".option");
    var span = opt ? opt.querySelector(".option-text") : null;
    return span ? span.innerHTML : "";
  }

  function reviewCard(panel, i) {
    var qid = panel.dataset.questionId;
    var points = Math.max(0, parseInt(panel.dataset.points || "0", 10) || 0);
    var chosen = null;
    var correct = null;
    panel.querySelectorAll(".answer-radio").forEach(function (r) {
      if (r.checked) chosen = r;
      if (r.dataset.correct === "1") correct = r;
    });
    var isCorrect = !!(chosen && chosen.dataset.correct === "1");

    var card = document.createElement("article");
    card.className = "card";
    var body = document.createElement("div");
    body.className = "card-body";
    card.appendChild(body);

    var head = document.createElement("div");
    head.className = "review-head";
    var title = document.createElement("h2");
    title.className = "question-title";
    title.textContent = Q("Question") + " " + (i + 1);
    head.appendChild(title);
    var pts = document.createElement("span");
    pts.className = "chip chip-pts";
    pts.textContent = "★ " + points + " " + Q("pts");
    head.appendChild(pts);
    body.appendChild(head);

    var qt = panel.querySelector(".question-text");
    if (qt) {
      var qclone = qt.cloneNode(true);
      qclone.classList.remove("mb-3");
      body.appendChild(qclone);
    }

    var list = document.createElement("ul");
    list.className = "review-list";

    var your = document.createElement("li");
    your.className =
      "answer-item " + (isCorrect ? "answer-item-good" : "answer-item-bad");
    var ylabel = document.createElement("span");
    ylabel.className = "answer-label " + (isCorrect ? "text-good" : "text-bad");
    ylabel.textContent = Q("Your answer");
    your.appendChild(ylabel);
    var yvalue = document.createElement("div");
    if (chosen) {
      yvalue.innerHTML = optionText(chosen);
    } else {
      yvalue.textContent = Q("Not answered");
    }
    your.appendChild(yvalue);
    list.appendChild(your);

    if (correct) {
      var cvalue = document.createElement("span");
      cvalue.className = "small";
      if (isCorrect) {
        cvalue.textContent = "+" + points + " " + Q("pts");
        cvalue.style.color = "var(--good)";
      } else {
        cvalue.textContent = "0 " + Q("pts");
        cvalue.style.color = "var(--bad)";
      }
      your.appendChild(cvalue);
    }

    if (!isCorrect) {
      var right = document.createElement("li");
      right.className = "answer-item answer-item-good";
      var rlabel = document.createElement("span");
      rlabel.className = "answer-label text-good";
      rlabel.textContent = Q("Correct answer");
      right.appendChild(rlabel);
      var rvalue = document.createElement("div");
      rvalue.innerHTML = optionText(correct);
      right.appendChild(rvalue);
      list.appendChild(right);
    }

    body.appendChild(list);
    return card;
  }

  function buildResults() {
    var earned = 0;
    var correctCount = 0;
    var frag = document.createDocumentFragment();
    panels.forEach(function (panel, i) {
      var chosen = null;
      panel.querySelectorAll(".answer-radio").forEach(function (r) {
        if (r.checked) chosen = r;
      });
      var isCorrect = !!(chosen && chosen.dataset.correct === "1");
      if (isCorrect) {
        earned += Math.max(0, parseInt(panel.dataset.points || "0", 10) || 0);
        correctCount += 1;
      }
      frag.appendChild(reviewCard(panel, i));
    });
    resultsBody.innerHTML = "";
    resultsBody.appendChild(frag);
    resultsSummary.textContent = Qf("Your score: {earned} / {total}", {
      earned: earned,
      total: totalPoints,
    });
    resultsCorrect.textContent = Qf("Correct answers: {correct} of {total}", {
      correct: correctCount,
      total: panels.length,
    });
  }

  function showResults() {
    buildResults();
    clearTimeout(timerHandle);
    zone.classList.add("d-none");
    results.classList.remove("d-none");
    window.scrollTo(0, 0);
  }

  function submitNow(timedOut) {
    if (submitting) return;
    var missing = panels.filter(function (p) {
      return !answered.has(p.dataset.questionId);
    });
    if (!timedOut && missing.length > 0) {
      unansweredList.innerHTML = "";
      missing.forEach(function (p) {
        var li = document.createElement("li");
        li.textContent = "#" + (panels.indexOf(p) + 1);
        unansweredList.appendChild(li);
        p.classList.add("is-unanswered");
      });
      alertBox.classList.remove("d-none");
      show(panels.indexOf(missing[0]));
      return;
    }

    submitting = true;
    if (timerHandle) clearInterval(timerHandle);
    done = true;
    writeStorage({ answers: answers, endTime: endTime, done: done });
    resultsNote.textContent = timedOut
      ? Q("Time's up! Your answers were submitted.")
      : "";
    showResults();
  }

  btnPrev.addEventListener("click", function () {
    show(index - 1);
  });
  btnNext.addEventListener("click", function () {
    show(index + 1);
  });
  btnSubmit.addEventListener("click", function () {
    submitNow(false);
  });
  btnRetake.addEventListener("click", function () {
    answers = {};
    answered = new Set();
    endTime = null;
    done = false;
    clearStorage();
    radios.forEach(function (r) {
      r.checked = false;
      r.disabled = false;
    });
    panels.forEach(function (p) {
      p.classList.remove("is-unanswered");
    });
    alertBox.classList.add("d-none");
    results.classList.add("d-none");
    zone.classList.remove("d-none");
    submitting = false;
    btnSubmit.disabled = false;
    index = 0;
    if (timeLimit > 0) {
      startTimer();
    }
    show(0);
  });

  if (done) {
    showResults();
    return;
  }

  if (timeLimit > 0) {
    startTimer();
    renderTimer(remainingNow());
  }

  show(0);
})();