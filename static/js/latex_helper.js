(function () {
  var OPTIONS = {
    throwOnError: false,
    delimiters: [
      { left: "$$", right: "$$", display: true },
      { left: "\\(", right: "\\)", display: false },
      { left: "\\[", right: "\\]", display: true },
      { left: "$", right: "$", display: false },
    ],
  };

  var PH = "[type in here]";

  var TEMPLATES = [
    {
      label: "Bold text",
      latex: "\\textbf{word}",
      copy: "\\textbf{" + PH + "}",
    },
    {
      label: "Red text",
      latex: "\\textcolor{red}{word}",
      copy: "\\textcolor{red}{" + PH + "}",
    },
    {
      label: "Blue text",
      latex: "\\textcolor{blue}{word}",
      copy: "\\textcolor{blue}{" + PH + "}",
    },
    {
      label: "Green text",
      latex: "\\textcolor{green}{word}",
      copy: "\\textcolor{green}{" + PH + "}",
    },
    {
      label: "Italic text",
      latex: "\\textit{word}",
      copy: "\\textit{" + PH + "}",
    },
    {
      label: "Fraction",
      latex: "\\frac{a}{b}",
      copy: "\\frac{" + PH + "}{" + PH + "}",
    },
    { label: "Power", latex: "x^2", copy: PH + "^{" + PH + "}" },
    { label: "Subscript", latex: "x_i", copy: PH + "_{" + PH + "}" },
    {
      label: "Square root",
      latex: "\\sqrt{x}",
      copy: "\\sqrt{" + PH + "}",
    },
    {
      label: "nth root",
      latex: "\\sqrt[n]{x}",
      copy: "\\sqrt[n]{" + PH + "}",
    },
    { label: "Vector", latex: "\\vec{F}", copy: "\\vec{" + PH + "}" },
    {
      label: "Dot product",
      latex: "\\vec{a} \\cdot \\vec{b}",
      copy: "\\vec{" + PH + "} \\cdot \\vec{" + PH + "}",
    },
    {
      label: "Integral",
      latex: "\\int_{a}^{b} f(x)\\,dx",
      copy: "\\int_{" + PH + "}^{" + PH + "} " + PH + "\\,dx",
    },
    {
      label: "Sum",
      latex: "\\sum_{i=1}^{n} i",
      copy: "\\sum_{i=" + PH + "}^{" + PH + "} " + PH,
    },
    {
      label: "Limit",
      latex: "\\lim_{x \\to 0} \\frac{\\sin x}{x}",
      copy: "\\lim_{" + PH + " \\to " + PH + "} " + PH,
    },
    {
      label: "Function",
      latex: "f(x) = x^2 + 1",
      copy: "f(" + PH + ") = " + PH,
    },
    { label: "Maps to", latex: "x \\mapsto f(x)", copy: PH + " \\mapsto " + PH },
    { label: "Sine", latex: "\\sin(x)", copy: "\\sin(" + PH + ")" },
    { label: "Cosine", latex: "\\cos(x)", copy: "\\cos(" + PH + ")" },
    { label: "Tangent", latex: "\\tan(x)", copy: "\\tan(" + PH + ")" },
    { label: "Natural log", latex: "\\ln(x)", copy: "\\ln(" + PH + ")" },
    {
      label: "Log (base b)",
      latex: "\\log_{b}(x)",
      copy: "\\log_{" + PH + "}(" + PH + ")",
    },
    { label: "Exponential", latex: "e^{x}", copy: "e^{" + PH + "}" },
    {
      label: "Absolute value",
      latex: "\\lvert x \\rvert",
      copy: "\\lvert " + PH + " \\rvert",
    },
    {
      label: "Floor",
      latex: "\\lfloor x \\rfloor",
      copy: "\\lfloor " + PH + " \\rfloor",
    },
    {
      label: "Ceiling",
      latex: "\\lceil x \\rceil",
      copy: "\\lceil " + PH + " \\rceil",
    },
    { label: "Greek: alpha", latex: "\\alpha" },
    { label: "Greek: beta", latex: "\\beta" },
    { label: "Greek: theta", latex: "\\theta" },
    { label: "Greek: pi", latex: "\\pi" },
    { label: "Greek: omega", latex: "\\omega" },
    { label: "Greek: Delta", latex: "\\Delta" },
    { label: "Plus / minus", latex: "\\pm" },
    { label: "Infinity", latex: "\\infty" },
    { label: "Approximately", latex: "\\approx" },
    { label: "Not equal", latex: "\\neq" },
    { label: "Less or equal", latex: "\\leq" },
    { label: "Greater or equal", latex: "\\geq" },
    {
      label: "Matrix",
      latex: "\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}",
      copy:
        "\\begin{pmatrix} " + PH + " & " + PH + " \\\\ " + PH + " & " + PH + " \\end{pmatrix}",
    },
    {
      label: "Piecewise",
      latex: "\\begin{cases} x & x > 0 \\\\ -x & x \\leq 0 \\end{cases}",
      copy:
        "\\begin{cases} " + PH + " & " + PH + " \\\\ " + PH + " & " + PH + " \\end{cases}",
    },
  ];

  // Arabic translations for the cheatsheet template labels.
  var AR_LABELS = {
    "Bold text": "نص عريض",
    "Red text": "نص أحمر",
    "Blue text": "نص أزرق",
    "Green text": "نص أخضر",
    "Italic text": "نص مائل",
    "Fraction": "كسر",
    "Power": "أسّ",
    "Subscript": "دليل سفلي",
    "Square root": "جذر تربيعي",
    "nth root": "جذر من الدرجة n",
    "Vector": "متجه",
    "Dot product": "جداء نقطي",
    "Integral": "تكامل",
    "Sum": "مجموع",
    "Limit": "نهاية",
    "Function": "دالة",
    "Maps to": "يُطابِق إلى",
    "Sine": "جيب الزاوية",
    "Cosine": "جيب تمام الزاوية",
    "Tangent": "ظل الزاوية",
    "Natural log": "لوغاريتم طبيعي",
    "Log (base b)": "لوغاريتم (أساس b)",
    "Exponential": "أُسّي",
    "Absolute value": "قيمة مطلقة",
    "Floor": "تقريب للأسفل",
    "Ceiling": "تقريب للأعلى",
    "Greek: alpha": "اليونانية: ألفا",
    "Greek: beta": "اليونانية: بيتا",
    "Greek: theta": "اليونانية: ثيتا",
    "Greek: pi": "اليونانية: باي",
    "Greek: omega": "اليونانية: أوميغا",
    "Greek: Delta": "اليونانية: دلتا",
    "Plus / minus": "زائد / ناقص",
    "Infinity": "لا نهائية",
    "Approximately": "تقريباً",
    "Not equal": "لا يساوي",
    "Less or equal": "أصغر من أو يساوي",
    "Greater or equal": "أكبر من أو يساوي",
    "Matrix": "مصفوفة",
    "Piecewise": "دالة مقطعية",
  };

  var currentLang = window.QUIZ_LANG || "en";

  function labelFor(t) {
    if (currentLang === "ar" && AR_LABELS[t.label]) {
      return AR_LABELS[t.label];
    }
    return t.label;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function mathContext(text) {
    var inMath = false;
    var i = 0;
    var n = text.length;
    while (i < n) {
      var two = text.slice(i, i + 2);
      if (two === "$$") {
        inMath = !inMath;
        i += 2;
      } else if (text[i] === "$") {
        inMath = !inMath;
        i += 1;
      } else if (two === "\\(" || two === "\\[") {
        inMath = true;
        i += 2;
      } else if (two === "\\)" || two === "\\]") {
        inMath = false;
        i += 2;
      } else {
        i += 1;
      }
    }
    return inMath;
  }

  function startsInsideMath(text) {
    var i = 0;
    var n = text.length;
    while (i < n) {
      var two = text.slice(i, i + 2);
      if (two === "\\(" || two === "\\[") return false;
      if (two === "$$" || text[i] === "$" || two === "\\)" || two === "\\]") {
        return true;
      }
      i += 1;
    }
    return false;
  }

  function unwrapSnippet(snippet) {
    if (!snippet) return { bare: "", stripLeading: "", stripTrailing: "" };
    if (snippet.slice(0, 2) === "$$" && snippet.slice(-2) === "$$") {
      return { bare: snippet.slice(2, -2), stripLeading: "$$", stripTrailing: "$$" };
    }
    if (snippet[0] === "$" && snippet[snippet.length - 1] === "$") {
      return { bare: snippet.slice(1, -1), stripLeading: "$", stripTrailing: "$" };
    }
    if (snippet.slice(0, 2) === "\\(" && snippet.slice(-2) === "\\)") {
      return { bare: snippet.slice(2, -2), stripLeading: "\\(", stripTrailing: "\\)" };
    }
    if (snippet.slice(0, 2) === "\\[" && snippet.slice(-2) === "\\]") {
      return { bare: snippet.slice(2, -2), stripLeading: "\\[", stripTrailing: "\\]" };
    }
    return { bare: snippet, stripLeading: "", stripTrailing: "" };
  }

  function mergeMath(existing, start, end, snippet) {
    if (start == null) start = existing.length;
    if (end == null) end = start;
    var before = existing.slice(0, start);
    var after = existing.slice(end);
    var u = unwrapSnippet(snippet);
    var inside = mathContext(before);
    var keepLeading = u.stripLeading ? !inside : true;
    var keepTrailing = u.stripTrailing
      ? !(inside && startsInsideMath(after))
      : true;
    var insertText =
      (keepLeading ? u.stripLeading : "") +
      u.bare +
      (keepTrailing ? u.stripTrailing : "");
    return {
      text: before + insertText + after,
      cursor: start + insertText.length,
    };
  }

  function wrapped(latex) {
    return "$" + latex + "$";
  }

  function render(element) {
    if (typeof renderMathInElement === "undefined") return;
    renderMathInElement(element, OPTIONS);
  }

  function renderLines(element, lines) {
    element.innerHTML = lines
      .map(function (line) {
        return (
          '<div class="mb-1 math-preview-line">' + escapeHtml(line) + "</div>"
        );
      })
      .join("");
    render(element);
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text);
    } else {
      var ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
  }

  function flash(btn) {
    var original = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-check me-1"></i> ' + Q("Copied!");
    setTimeout(function () {
      btn.innerHTML = original;
    }, 1200);
  }

  function buildCheatsheet(container) {
    container.dataset.built = "1";
    container.innerHTML =
      '<div class="row g-2">' +
      TEMPLATES.map(function (t, i) {
        return (
          '<div class="col-6 col-md-4 col-lg-3">' +
          '<div class="card card-body py-2 px-3 h-100">' +
           '<div class="small text-muted">' + escapeHtml(labelFor(t)) + "</div>" +
          '<div class="math-template-preview mt-1">' +
          escapeHtml(wrapped(t.latex)) +
          "</div>" +
          '<button type="button" class="btn btn-sm btn-outline-primary mt-1 copy-template" data-index="' +
          i +
          '"><i class="fa-solid fa-copy me-1"></i> ' + Q("Copy") + "</button>" +
          "</div></div>"
        );
      }).join("") +
      "</div>";

    container.querySelectorAll(".math-template-preview").forEach(render);
    container.querySelectorAll(".copy-template").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var t = TEMPLATES[parseInt(btn.dataset.index, 10)];
        copy(wrapped(t.copy || t.latex));
        flash(btn);
      });
    });
  }

  function setLanguage(lang) {
    currentLang = lang || "en";
    document.querySelectorAll(".cheatsheet").forEach(function (el) {
      if (el.dataset.built) {
        buildCheatsheet(el);
      }
    });
  }

  window.LaTeXHelper = {
    OPTIONS: OPTIONS,
    TEMPLATES: TEMPLATES,
    AR_LABELS: AR_LABELS,
    escapeHtml: escapeHtml,
    render: render,
    renderLines: renderLines,
    copy: copy,
    buildCheatsheet: buildCheatsheet,
    mergeMath: mergeMath,
    setLanguage: setLanguage,
  };
})();
