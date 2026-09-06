(function () {
  const container = document.getElementById("questions-container");
  const btnAdd = document.getElementById("btn-add-question");
  const accessWrap = document.getElementById("access-code-wrap");
  const publicToggle = document.getElementById("is-public");
  const enableTimeLimit = document.getElementById("enable-time-limit");
  const timeLimitInput = document.getElementById("time-limit-input");
  const maxQuestions = 50;
  const khatt = !!(window.KHATT_HELPER && window.KHATT_HELPER.isActive());
  const mathLabel = khatt ? Q("Math (Arabic)") : Q("Math (LaTeX)");
  const guideLabel = khatt ? Q("Symbols & templates") : Q("LaTeX guide & templates");

  function qName(idx, field) {
    return "questions-" + idx + "-" + field;
  }
  function aName(idx, aIdx, field) {
    return "questions-" + idx + "-answers-" + aIdx + "-" + field;
  }

  function collectBlock(block) {
    const idx = parseInt(block.dataset.index, 10);
    const q = {
      text: block.querySelector('textarea[name="' + qName(idx, "text") + '"]').value,
      points: block.querySelector('input[name="' + qName(idx, "points") + '"]').value,
      image: block.querySelector('input[name="' + qName(idx, "image") + '"]').files[0] || null,
      math: block.querySelector('input[name="' + qName(idx, "math") + '"]').checked,
      answers: Array.from(block.querySelectorAll(".answer-row")).map((row, aIdx) => ({
        text: row.querySelector('input[name="' + aName(idx, aIdx, "text") + '"]').value,
        correct: row.querySelector('input[name="' + aName(idx, aIdx, "correct") + '"]').checked,
      })),
    };
    return q;
  }

  function collectAll() {
    return Array.from(container.querySelectorAll(".question-block")).map(collectBlock);
  }

  function buildBlock(idx, q) {
    const div = document.createElement("div");
    div.className = "card shadow-sm mb-3 question-block";
    div.dataset.index = idx;
    div.innerHTML =
      '<div class="card-header d-flex justify-content-between align-items-center">' +
      '<span class="fw-semibold">' + Q("Question") + " " + (idx + 1) + "</span>" +
      '<button type="button" class="btn btn-sm btn-outline-danger remove-question">' +
      '<i class="fa-solid fa-trash"></i></button></div>' +
      '<div class="card-body">' +
      '<div class="row g-3 mb-3">' +
      '<div class="col-md-8">' +
      '<label class="form-label">' + Q("Question text") + "</label>" +
      '<textarea name="' + qName(idx, "text") + '" class="form-control" rows="2" required>' +
      (q && q.text ? q.text : "") + "</textarea></div>" +
      '<div class="col-md-4">' +
      '<label class="form-label">' + Q("Points") + "</label>" +
      '<input type="number" name="' + qName(idx, "points") + '" class="form-control" min="1" required value="' +
      (q && q.points ? q.points : 10) + '"></div>' +
      '<div class="col-md-8">' +
      '<label class="form-label">' + Q("Optional image") + "</label>" +
      '<input type="file" name="' + qName(idx, "image") + '" class="form-control" accept="image/*"></div>' +
      '<div class="col-md-4 d-flex align-items-end">' +
      '<div class="form-check form-switch">' +
      '<input type="checkbox" class="form-check-input" name="' + qName(idx, "math") + '" id="' + qName(idx, "math") + '"' +
      (q && q.math ? " checked" : "") + ">" +
      '<label class="form-check-label" for="' + qName(idx, "math") + '">' + mathLabel + "</label></div>" +
      "</div>" +
      "</div>" +
      '<div class="answers-list"></div>' +
      '<button type="button" class="btn btn-sm btn-outline-primary add-answer">' +
      '<i class="fa-solid fa-circle-plus me-1"></i> ' + Q("Add answer") + "</button>" +
      '<div class="mt-3 d-none math-helper">' +
      '<hr>' +
      '<button type="button" class="btn btn-sm btn-outline-secondary toggle-cheatsheet">' +
      '<i class="fa-solid fa-book-open me-1"></i> ' + guideLabel + "</button>" +
      '<div class="cheatsheet d-none mt-2"></div>' +
      '<label class="form-label mt-3 mb-1">' + Q("Live preview") + "</label>" +
      '<div class="preview-box border rounded p-2 bg-white"></div>' +
      '<div class="math-warning text-danger small d-none mt-1"></div>' +
      "</div>" +
      "</div>";

    const answersList = div.querySelector(".answers-list");
    const mathToggle = div.querySelector('input[name="' + qName(idx, "math") + '"]');
    const mathHelper = div.querySelector(".math-helper");
    const cheatsheet = div.querySelector(".cheatsheet");
    const preview = div.querySelector(".preview-box");
    const warning = div.querySelector(".math-warning");

    function refreshPreview() {
      if (!mathToggle.checked) return;
      const q = collectBlock(div);
      const lines = [q.text].concat(q.answers.map((a) => a.text));
      const content = lines.join("\n\n");
      // Arabic mode always renders through Khatt; in LaTeX mode fall back to
      // images only when the stored content actually contains khatt.org imgs
      // (e.g. an Arabic-authored quiz being edited while the UI is English).
      if (
        window.KHATT_HELPER &&
        (khatt || window.KHATT_HELPER.sanitize(content).indexOf("<img") !== -1)
      ) {
        window.KHATT_HELPER.renderRich(preview, content);
        warning.classList.add("d-none");
        return;
      }
      if (!window.LaTeXHelper) return;
      window.LaTeXHelper.renderLines(preview, lines);
      const hasErrors = preview.querySelector(".katex-error") !== null;
      warning.classList.toggle("d-none", !hasErrors);
      warning.textContent = hasErrors
        ? Q("Some formulas contain errors. Fix them before saving.")
        : "";
    }

    if (!khatt && window.LaTeXHelper) {
      window.LaTeXHelper.buildCheatsheet(cheatsheet);
    }

    function syncHelper() {
      mathHelper.classList.toggle("d-none", !mathToggle.checked);
      if (mathToggle.checked) refreshPreview();
    }

    mathToggle.addEventListener("change", syncHelper);
    div.querySelector(".toggle-cheatsheet").addEventListener("click", () => {
      const hidden = cheatsheet.classList.toggle("d-none");
      if (!hidden && khatt && window.KHATT_HELPER) {
        window.KHATT_HELPER.reveal(cheatsheet);
      }
    });
    div.addEventListener("input", (event) => {
      if (
        mathToggle.checked &&
        (event.target.matches("textarea") ||
          event.target.matches(".answer-row input"))
      ) {
        clearTimeout(div._previewTimer);
        div._previewTimer = setTimeout(refreshPreview, 300);
      }
    });
    div.addEventListener("paste", (event) => {
      if (khatt || !mathToggle.checked || !window.LaTeXHelper) return;
      const target = event.target;
      const editable =
        target.matches("textarea") || target.matches(".answer-row input[type='text']");
      if (!editable) return;
      event.preventDefault();
      const snippet = (event.clipboardData || window.clipboardData).getData("text");
      const start =
        target.selectionStart != null ? target.selectionStart : target.value.length;
      const end =
        target.selectionEnd != null ? target.selectionEnd : start;
      const result = window.LaTeXHelper.mergeMath(
        target.value,
        start,
        end,
        snippet
      );
      target.value = result.text;
      target.setSelectionRange(result.cursor, result.cursor);
      refreshPreview();
    });

    const addAnswer = (a) => {
      answersList.appendChild(buildAnswerRow(idx, answersList.children.length, a));
    };
    div.querySelector(".add-answer").addEventListener("click", () => addAnswer(null));
    div.querySelector(".remove-question").addEventListener("click", () => {
      removeBlock(idx);
    });

    if (q && q.answers && q.answers.length) {
      q.answers.forEach(addAnswer);
    } else {
      addAnswer(null);
      addAnswer(null);
    }
    syncHelper();
    return div;
  }

  function buildAnswerRow(idx, aIdx, a) {
    const row = document.createElement("div");
    row.className = "input-group mb-2 answer-row";
    row.innerHTML =
      '<input type="text" name="' + aName(idx, aIdx, "text") + '" class="form-control" placeholder="' + Q("Answer text") + '" required value="' +
      (a && a.text ? a.text : "") + '">' +
      '<div class="input-group-text">' +
      '<input type="checkbox" name="' + aName(idx, aIdx, "correct") + '" class="form-check-input mt-0"' +
      (a && a.correct ? " checked" : "") + ">" +
      '<label class="ms-1 mb-0"> ' + Q("correct") + "</label></div>" +
      '<button type="button" class="btn btn-outline-danger remove-answer"><i class="fa-solid fa-xmark"></i></button>';
    row.querySelector(".remove-answer").addEventListener("click", () => {
      row.remove();
      rebuild();
    });
    return row;
  }

  function render(blocks) {
    container.innerHTML = "";
    blocks.forEach((q, idx) => container.appendChild(buildBlock(idx, q)));
  }

  function rebuild() {
    const blocks = collectAll();
    render(blocks);
  }

  function removeBlock(idx) {
    const blocks = collectAll();
    blocks.splice(idx, 1);
    render(blocks);
  }

  btnAdd.addEventListener("click", () => {
    const count = container.querySelectorAll(".question-block").length;
    if (count >= maxQuestions) {
      alert(Q("Maximum {n} questions.").replace("{n}", maxQuestions));
      return;
    }
    container.appendChild(buildBlock(count, null));
  });

  publicToggle.addEventListener("change", () => {
    accessWrap.classList.toggle("d-none", publicToggle.checked);
  });
  accessWrap.classList.toggle("d-none", publicToggle.checked);

  function syncTimeLimit() {
    const enabled = enableTimeLimit.checked;
    timeLimitInput.disabled = !enabled;
    if (!enabled) timeLimitInput.value = "";
  }
  enableTimeLimit.addEventListener("change", syncTimeLimit);
  if (timeLimitInput.value) enableTimeLimit.checked = true;
  syncTimeLimit();

  if (khatt && window.KHATT_HELPER) {
    container.addEventListener("focusin", (event) => {
      const target = event.target;
      if (
        target.matches("textarea") ||
        target.matches(".answer-row input[type='text']")
      ) {
        window.KHATT_HELPER.setActiveTarget(target);
      }
    });
  }
})();
