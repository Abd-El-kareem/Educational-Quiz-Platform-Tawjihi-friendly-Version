(function () {
  function csrfToken() {
    const name = "csrftoken=";
    const decoded = decodeURIComponent(document.cookie);
    for (const cookie of decoded.split(";")) {
      let c = cookie.trim();
      if (c.indexOf(name) === 0) return c.substring(name.length);
    }
    return "";
  }

  document.querySelectorAll(".ask-ai").forEach((btn) => {
    btn.addEventListener("click", () => {
      const panel =
        btn.closest(".question-panel") || btn.closest(".card");
      const out = panel.querySelector(".ai-answer");
      const url = btn.dataset.url;

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> ' + Q("Asking AI…");
      out.classList.remove("d-none");
      out.innerHTML = '<div class="alert alert-light mb-0 text-muted">' + Q("Thinking…") + "</div>";

      const options = { method: "POST", headers: { "X-CSRFToken": csrfToken() } };
      const scoreId = btn.dataset.scoreId;
      if (scoreId) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify({ score_id: scoreId });
      }

      fetch(url, options)
        .then((res) => {
          if (!res.ok) return res.json().then((err) => Promise.reject(err));
          return res.json();
        })
        .then((data) => {
          out.innerHTML = data.html;
          if (typeof renderMathInElement !== "undefined") {
            renderMathInElement(out, {
              throwOnError: false,
              delimiters: [
                { left: "$$", right: "$$", display: true },
                { left: "\\(", right: "\\)", display: false },
                { left: "\\[", right: "\\]", display: true },
                { left: "$", right: "$", display: false },
              ],
            });
          }
        })
        .catch((err) => {
          out.innerHTML =
            '<div class="alert alert-warning mb-0">' +
            (err.detail || Q("Could not generate an explanation.")) +
            "</div>";
        })
        .finally(() => {
          btn.disabled = false;
          btn.innerHTML = '<i class="fa-solid fa-robot me-1"></i> ' + Q("Ask AI");
        });
    });
  });
})();
