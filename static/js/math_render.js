(function () {
  if (typeof renderMathInElement === "undefined") return;
  var options = {
    throwOnError: false,
    delimiters: [
      { left: "$$", right: "$$", display: true },
      { left: "\\(", right: "\\)", display: false },
      { left: "\\[", right: "\\]", display: true },
      { left: "$", right: "$", display: false },
    ],
  };
  document.querySelectorAll(".math-content").forEach(function (el) {
    renderMathInElement(el, options);
  });
})();
