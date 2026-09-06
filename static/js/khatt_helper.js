(function () {
  "use strict";

  var API = "https://khatt.org/api?c=";
  var engine = window.QUIZ_LANG === "ar" ? "khatt" : "katex";

  /* ------------------------------------------------------------------ *
   * Template catalog.  Each structure template is a Khatt command with
   * {0}, {1}, ... placeholders; `sample` fills them with concrete values so
   * the palette can render a real preview thumbnail via the Khatt API.
   * `literals` insert immediately with no modal.
   * ------------------------------------------------------------------ */
  var STRUCTURE = [
    {
      g: "Structure",
      key: "fraction",
      ar: "كسر",
      cmd: "/على{{0}}{{1}}",
      sample: "/على{س + 1}{2}",
      ph: ["البسط", "المقام"],
    },
    {
      g: "Structure",
      key: "sqrt",
      ar: "جذر تربيعي",
      cmd: "/جذر{{0}}",
      sample: "/جذر{س + 1}",
      ph: ["التعبير"],
    },
    {
      g: "Structure",
      key: "nth-root",
      ar: "جذر من الدرجة ن",
      cmd: "/جذر{{0}}{{1}}",
      sample: "/جذر{3}{س}",
      ph: ["الدرجة", "التعبير"],
    },
    {
      g: "Structure",
      key: "power",
      ar: "أس",
      cmd: "{{0}}^{{1}}",
      sample: "{س}^{2}",
      ph: ["الأساس", "الأس"],
    },
    {
      g: "Structure",
      key: "sum",
      ar: "مجموع",
      cmd: "/مج{{0}}{{1}}",
      sample: "/مج{س + 1}{ص + 1}",
      ph: ["السفلي", "العلوي"],
    },
    {
      g: "Structure",
      key: "integral",
      ar: "تكامل",
      cmd: "/تكا{{0}}{{1}}",
      sample: "/تكا{س + 1}{ص + 1}",
      ph: ["السفلي", "العلوي"],
    },
    {
      g: "Structure",
      key: "limit",
      ar: "نهاية",
      cmd: "/نها{{0}}{{1}}",
      sample: "/نها{س + 1}{ص + 1}",
      ph: ["التعبير الأول", "التعبير الثاني"],
    },
    {
      g: "Structure",
      key: "bracket",
      ar: "قوس",
      cmd: "/قوس {{0}}",
      sample: "/قوس {1 + 2}",
      ph: ["التعبير"],
    },
    {
      g: "Structure",
      key: "matrix",
      ar: "مصفوفة 2×2",
      cmd: "/مصفوفة\n{{{0}}{{1}}}\n{{{2}}{{3}}}",
      sample: "/مصفوفة\n{{1}{2}}\n{{3}{4}}",
      ph: ["العنصر 11", "العنصر 12", "العنصر 21", "العنصر 22"],
    },
  ];

  var LITERALS = [
    { g: "Operators", ar: "زائد +", cmd: "+" },
    { g: "Operators", ar: "ناقص −", cmd: "-" },
    { g: "Operators", ar: "زائد ناقص ±", cmd: "/.زائد.ناقص" },
    { g: "Operators", ar: "ضرب ×", cmd: "/.ضرب" },
    { g: "Operators", ar: "قسمة ÷", cmd: "/.قسمة" },
    { g: "Operators", ar: "تقاطع ∩", cmd: "/.تقاطع" },
    { g: "Operators", ar: "اتحاد ∪", cmd: "/.اتحاد" },
    { g: "Relations", ar: "باي π", cmd: "/.باي" },
    { g: "Relations", ar: "لا نهاية ∞", cmd: "/.لا.نهاية" },
    { g: "Relations", ar: "أكبر أو يساوي ≥", cmd: "/.أكبر.يساوي" },
    { g: "Relations", ar: "أصغر أو يساوي ≤", cmd: "/.أصغر.يساوي" },
    { g: "Relations", ar: "لا يساوي ≠", cmd: "/.لا.يساوي" },
    { g: "Relations", ar: "يساوي تقريباً ≈", cmd: "/.يساوي.تقريبا" },
    { g: "Relations", ar: "ينتمي ∈", cmd: "/.ينتمي" },
    { g: "Relations", ar: "خالية ∅", cmd: "/.خالية" },
    { g: "Relations", ar: "يوجد ∃", cmd: "/.يوجد" },
    { g: "Arrows", ar: "سهم يمين →", cmd: "/.سهم.يمين" },
    { g: "Arrows", ar: "سهم يسار ←", cmd: "/.سهم.يسار" },
    { g: "Formatting", ar: "مسافة", cmd: "/مسافة" },
  ];

  var GROUP_LABELS = {
    Structure: "البنية",
    Operators: "العمليات",
    Relations: "العلاقات",
    Arrows: "الأسهم",
    Formatting: "التنسيق",
  };

  /* ------------------------------------------------------------------ */
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttr(str) {
    return escapeHtml(str);
  }

  function url(command) {
    return API + encodeURIComponent(command);
  }

  function fill(tpl, values) {
    return String(tpl.cmd || tpl).replace(/\{(\d+)\}/g, function (_, n) {
      var v = values[+n];
      return v == null ? "" : v;
    });
  }

  function extractAttr(tag, name) {
    var re = new RegExp(name + '\\s*=\\s*(?:"([^"]*)"|\'([^\']*)\'|([^\\s>]+))', "i");
    var m = tag.match(re);
    return m ? m[1] || m[2] || m[3] || "" : "";
  }

  function safeImgTag(tag) {
    var src = extractAttr(tag, "src");
    if (src.indexOf("khatt.org/api?c=") === -1) return "";
    var w = extractAttr(tag, "width");
    var h = extractAttr(tag, "height");
    var alt = extractAttr(tag, "alt");
    var out = '<img src="' + escapeAttr(src) + '"';
    if (/^\d+$/.test(w)) out += ' width="' + w + '"';
    if (/^\d+$/.test(h)) out += ' height="' + h + '"';
    if (alt) out += ' alt="' + escapeAttr(alt) + '"';
    return out + ">";
  }

  /* Client-side twin of the server `rich` filter, used by the live preview:
   * keep only khatt.org <img> tags, escape everything else. */
  function sanitize(text) {
    var tokens = [];
    var stripped = String(text || "").replace(/<img\b[^>]*>/gi, function (m) {
      var safe = safeImgTag(m);
      tokens.push(safe);
      return "\u0000" + (tokens.length - 1) + "\u0000";
    });
    var escaped = escapeHtml(stripped);
    return escaped.replace(/\u0000(\d+)\u0000/g, function (_, i) {
      return tokens[+i];
    });
  }

  function renderRich(element, text) {
    element.innerHTML = sanitize(text);
  }

  /* ------------------------------------------------------------------ */
  var activeTarget = null;

  function setActiveTarget(el) {
    activeTarget = el;
  }

  function getActiveTarget() {
    if (activeTarget && activeTarget.isConnected) return activeTarget;
    return null;
  }

  function insertAtCursor(target, text) {
    var start =
      target.selectionStart != null ? target.selectionStart : target.value.length;
    var end = target.selectionEnd != null ? target.selectionEnd : start;
    var value = target.value;
    target.value = value.slice(0, start) + text + value.slice(end);
    var pos = start + text.length;
    target.setSelectionRange(pos, pos);
    target.focus();
    target.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function insertImg(command, alt, width, height) {
    var target = getActiveTarget();
    if (!target) return;
    var src = url(command);
    var makeTag = function (w, h) {
      var tag =
        '<img src="' +
        escapeAttr(src) +
        '"' +
        (w ? ' width="' + w + '"' : "") +
        (h ? ' height="' + h + '"' : "") +
        ' alt="' +
        escapeAttr(alt || "") +
        '">';
      insertAtCursor(target, tag);
    };
    if (width && height) {
      makeTag(width, height);
      return;
    }
    var img = new Image();
    img.onload = function () {
      makeTag(img.naturalWidth, img.naturalHeight);
    };
    img.onerror = function () {
      makeTag(null, null);
    };
    img.src = src;
  }

  function renderPreviewInto(imgEl, command) {
    imgEl.onload = null;
    imgEl.onerror = null;
    imgEl.src = url(command);
  }

  /* ------------------------------------------------------------------ */
  var modal = null;
  var modalTemplate = null;

  function ensureModal() {
    if (modal) return modal;
    modal = document.getElementById("khatt-modal");
    if (modal) return modal;

    modal = document.createElement("div");
    modal.className = "modal fade";
    modal.id = "khatt-modal";
    modal.tabIndex = -1;
    modal.setAttribute("aria-hidden", "true");
    modal.innerHTML =
      '<div class="modal-dialog">' +
      '<div class="modal-content">' +
      '<div class="modal-header">' +
      '<h5 class="modal-title" id="khatt-modal-title"></h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>' +
      "</div>" +
      '<div class="modal-body">' +
      '<div class="khatt-fields"></div>' +
      '<div class="d-flex justify-content-between align-items-end mt-3 mb-1">' +
      '<label class="form-label mb-0">' +
      (Q && Q("Raw command")) +
      "</label>" +
      '<a href="#" class="small khatt-reset-fields d-none">' +
      (Q && Q("Reset fields")) +
      "</a>" +
      "</div>" +
      '<textarea class="form-control khatt-raw" rows="2" dir="ltr" spellcheck="false" placeholder="/على{...}{...}"></textarea>' +
      '<div class="mt-2">' +
      '<label class="form-label small text-muted mb-1 d-block">' +
      (Q && Q("Symbols")) +
      "</label>" +
      '<div class="khatt-nested"></div>' +
      "</div>" +
      '<label class="form-label mt-3 mb-1">' +
      (Q && Q("Live preview")) +
      "</label>" +
      '<div class="border rounded p-2 bg-white text-center khatt-preview"></div>' +
      "</div>" +
      '<div class="modal-footer">' +
      '<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">' +
      (Q && Q("Cancel")) +
      "</button>" +
      '<button type="button" class="btn btn-primary khatt-insert">' +
      (Q && Q("Insert")) +
      "</button>" +
      "</div>" +
      "</div>" +
      "</div>";
    document.body.appendChild(modal);

    /* Persistent modal nodes: bind these listeners exactly once and read
     * the per-open state stored on the modal by openEditor(). */
    var rawEl = modal.querySelector(".khatt-raw");
    rawEl.addEventListener("input", function () {
      var st = modal._khattState;
      if (!st) return;
      st.setFieldsLocked(true);
      st.schedulePreview(rawEl.value);
    });
    rawEl.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        var st = modal._khattState;
        if (st) st.insert();
      }
    });
    modal.addEventListener("click", function (e) {
      if (!e.target || !e.target.classList.contains("khatt-reset-fields")) return;
      e.preventDefault();
      var st = modal._khattState;
      if (st) st.reset();
    });
    modal.querySelector(".khatt-insert").addEventListener("click", function () {
      var st = modal._khattState;
      if (st) st.insert();
    });

    return modal;
  }

  function openEditor(tpl) {
    var target = getActiveTarget();
    if (!target) {
      var firstBox = document.querySelector(
        "#questions-container textarea, #questions-container .answer-row input"
      );
      if (firstBox) setActiveTarget(firstBox);
    }
    modalTemplate = tpl;
    var node = ensureModal();

    var title = node.querySelector("#khatt-modal-title");
    title.textContent = Q ? Q(tpl.ar) : tpl.ar;

    var fields = node.querySelector(".khatt-fields");
    fields.innerHTML = "";
    var inputs = [];
    tpl.ph.forEach(function (label) {
      var wrap = document.createElement("div");
      wrap.className = "mb-2";
      wrap.innerHTML =
        '<label class="form-label mb-0 small">' +
        escapeHtml(label) +
        "</label>";
      var input = document.createElement("input");
      input.type = "text";
      input.className = "form-control";
      input.placeholder = label;
      wrap.appendChild(input);
      fields.appendChild(wrap);
      inputs.push(input);
    });

    var preview = node.querySelector(".khatt-preview");
    preview.innerHTML = "";
    var img = new Image();
    img.style.maxWidth = "100%";
    preview.appendChild(img);

    var raw = node.querySelector(".khatt-raw");
    raw.value = tpl.sample || "";
    raw.disabled = false;

    var resetBtn = node.querySelector(".khatt-reset-fields");

    function setFieldsLocked(locked) {
      inputs.forEach(function (i) {
        i.disabled = locked;
      });
      fields.classList.toggle("text-muted", locked);
      resetBtn.classList.toggle("d-none", !locked);
    }
    setFieldsLocked(false);

    var debounce = null;
    var lastUrl = null;
    function renderFor(cmd) {
      lastUrl = url(cmd);
      renderPreviewInto(img, cmd);
    }
    function schedulePreview(cmd) {
      clearTimeout(debounce);
      debounce = setTimeout(function () {
        renderFor(cmd);
      }, 350);
    }

    /* Part fields rebuild the template command into the raw textarea. */
    function regenFromFields() {
      var values = inputs.map(function (i) {
        return i.value;
      });
      var cmd = fill(tpl, values);
      raw.value = cmd;
      schedulePreview(cmd);
    }
    inputs.forEach(function (input) {
      input.addEventListener("input", function () {
        clearTimeout(debounce);
        debounce = setTimeout(regenFromFields, 200);
      });
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          node.querySelector(".khatt-insert").click();
        }
      });
    });

    /* A manual raw edit makes the raw text authoritative: lock the fields.
     * The listeners on `raw` and the Insert button live on the persistent
     * modal (see ensureModal()); here we only expose this open's state. */
    var state = {
      setFieldsLocked: setFieldsLocked,
      schedulePreview: schedulePreview,
      insert: doInsert,
      reset: function () {
        inputs.forEach(function (i) {
          i.value = "";
        });
        setFieldsLocked(false);
        raw.value = tpl.sample || "";
        schedulePreview(raw.value);
      },
    };
    node._khattState = state;

    /* Nested symbols: insert a sub-command at the raw textarea cursor. */
    var nested = node.querySelector(".khatt-nested");
    nested.innerHTML = "";
    function addNested(labelTxt, cmd) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "btn btn-sm btn-outline-secondary";
      b.textContent = labelTxt;
      b.title = cmd;
      b.addEventListener("click", function () {
        var start =
          raw.selectionStart != null ? raw.selectionStart : raw.value.length;
        var end = raw.selectionEnd != null ? raw.selectionEnd : start;
        raw.value = raw.value.slice(0, start) + cmd + raw.value.slice(end);
        var pos = start + cmd.length;
        raw.setSelectionRange(pos, pos);
        raw.focus();
        setFieldsLocked(true);
        schedulePreview(raw.value);
      });
      nested.appendChild(b);
    }
    STRUCTURE.forEach(function (t) {
      if (t.key !== tpl.key) addNested(t.ar, t.sample || "");
    });
    LITERALS.forEach(function (item) {
      addNested(item.ar, item.cmd);
    });

    function doInsert() {
      var cmd = String(raw.value || "").trim();
      if (!cmd) return;
      closeModal();
      if (url(cmd) === lastUrl && img.naturalWidth > 0) {
        insertImg(cmd, tpl.ar, img.naturalWidth, img.naturalHeight);
      } else {
        insertImg(cmd, tpl.ar);
      }
    }

    schedulePreview(raw.value);
    var bsModal =
      window.bootstrap && bootstrap.Modal.getOrCreateInstance(node);
    if (bsModal) bsModal.show();
  }

  function closeModal() {
    var node = ensureModal();
    var bsModal =
      window.bootstrap && bootstrap.Modal.getInstance(node);
    if (bsModal) bsModal.hide();
    document.body.classList.remove("modal-open");
    var backdrop = document.querySelector(".modal-backdrop");
    if (backdrop) backdrop.remove();
  }

  /* ------------------------------------------------------------------ */
  function literalButton(item) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "khatt-literal d-flex align-items-center gap-2 text-start";
    btn.title = item.ar;
    var img = new Image();
    img.loading = "lazy";
    img.dataset.khattSrc = url(item.cmd);
    img.alt = item.ar;
    img.style.maxHeight = "32px";
    btn.appendChild(img);
    btn.appendChild(document.createElement("span"));
    btn.lastChild.textContent = item.ar;
    btn.addEventListener("click", function () {
      var target = getActiveTarget();
      if (!target) {
        var firstBox = document.querySelector(
          "#questions-container textarea, #questions-container .answer-row input"
        );
        if (firstBox) setActiveTarget(firstBox);
      }
      insertImg(item.cmd, item.ar);
    });
    return btn;
  }

  function structButton(tpl) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "khatt-struct d-flex align-items-center gap-2 text-start";
    btn.title = tpl.ar;
    var img = new Image();
    img.loading = "lazy";
    img.dataset.khattSrc = url(tpl.sample);
    img.alt = tpl.ar;
    img.style.maxHeight = "32px";
    btn.appendChild(img);
    btn.appendChild(document.createElement("span"));
    btn.lastChild.textContent = tpl.ar;
    btn.addEventListener("click", function () {
      openEditor(tpl);
    });
    return btn;
  }

  function groupSection(label, buttons) {
    var section = document.createElement("div");
    section.className = "khatt-group mb-3";
    var title = document.createElement("h6");
    title.className = "text-muted text-uppercase small fw-bold";
    title.textContent = label;
    section.appendChild(title);
    var grid = document.createElement("div");
    grid.className = "khatt-grid";
    buttons.forEach(function (b) {
      grid.appendChild(b);
    });
    section.appendChild(grid);
    return section;
  }

  /* Build the symbol palette inside `container` (the cheatsheet div). */
  function buildPalette(container) {
    if (container.dataset.khattBuilt === "1") return;
    container.dataset.khattBuilt = "1";
    container.innerHTML = "";

    var groups = {};
    STRUCTURE.forEach(function (tpl) {
      (groups[tpl.g] = groups[tpl.g] || []).push(structButton(tpl));
    });
    LITERALS.forEach(function (item) {
      (groups[item.g] = groups[item.g] || []).push(literalButton(item));
    });
    Object.keys(groups).forEach(function (g) {
      container.appendChild(groupSection(GROUP_LABELS[g], groups[g]));
    });
  }

  /* Assign thumbnail src lazily — call only when the palette becomes
   * visible so no API request fires until the user opens the cheatsheet. */
  function reveal(container) {
    buildPalette(container);
    var imgs = container.querySelectorAll("img[data-khatt-src]");
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      if (!img.src) img.src = img.dataset.khattSrc;
    }
  }

  /* ------------------------------------------------------------------ */
  window.KHATT_HELPER = {
    isActive: function () {
      return engine === "khatt";
    },
    url: url,
    fill: fill,
    sanitize: sanitize,
    renderRich: renderRich,
    buildPalette: buildPalette,
    reveal: reveal,
    openEditor: openEditor,
    setActiveTarget: setActiveTarget,
    getActiveTarget: getActiveTarget,
    insertImg: insertImg,
  };
})();