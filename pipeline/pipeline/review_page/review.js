// Numeral review page (D-36). Local only: items.js is written by `python -m pipeline.review_numerals build`.
(function () {
  "use strict";
  var R = window.REVIEW;
  var KEY = "numeral-review:" + R.source;
  var answers = JSON.parse(localStorage.getItem(KEY) || "{}");
  var items = R.items;
  var view = [];
  var pos = 0;
  var $ = function (id) { return document.getElementById(id); };
  var CHARS = ["·", "½", "¼", "¾", "⅓", "⅔", "°", "′", "ā", "ī", "ū", "ṛ", "ṇ", "ṣ", "ṭ", "ḍ", "ñ", "ś", "—"];

  function store() { localStorage.setItem(KEY, JSON.stringify(answers)); }

  function rebuild(keepId) {
    var reason = $("filter").value, open = $("open-only").checked;
    view = items.filter(function (it) {
      return (!reason || it.reasons.indexOf(reason) >= 0) && (!open || !(it.id in answers) || it.id === keepId);
    });
    pos = Math.max(0, view.findIndex(function (it) { return it.id === keepId; }));
    show();
  }

  function show() {
    var done = items.filter(function (it) { return it.id in answers; }).length;
    $("progress").textContent = done + " of " + items.length + " answered" + (view.length ? " · item " + (pos + 1) + " of " + view.length + " shown" : "");
    var it = view[pos];
    if (!it) {
      $("where").textContent = "Nothing left in this view.";
      $("crop").removeAttribute("src");
      $("text").value = "";
      $("status").textContent = "";
      return;
    }
    $("where").textContent = "p. " + it.page + " (leaf " + it.leaf + ") · " + it.kind + (it.col ? " · right column" : "") + " · " + it.reasons.join(", ");
    $("crop").src = it.crop;
    $("text").value = it.id in answers ? answers[it.id] : it.text;
    $("status").textContent = it.id in answers ? (answers[it.id] === "" ? "Saved: delete this line." : "Saved.") : "";
    $("text").focus();
    $("text").setSelectionRange(0, 0);
    $("text").scrollTop = 0;
  }

  function move(d) { pos = Math.min(Math.max(0, pos + d), Math.max(0, view.length - 1)); show(); }

  function save() {
    var it = view[pos];
    if (!it) return;
    answers[it.id] = $("text").value.trim();
    store();
    if ($("open-only").checked) {
      view.splice(pos, 1);
      if (pos >= view.length) pos = Math.max(0, view.length - 1);
      show();
    } else {
      move(1);
    }
  }

  function insert(ch) {
    var t = $("text"), s = t.selectionStart, e = t.selectionEnd;
    t.value = t.value.slice(0, s) + ch + t.value.slice(e);
    t.focus();
    t.setSelectionRange(s + ch.length, s + ch.length);
  }

  var reasons = {};
  items.forEach(function (it) { it.reasons.forEach(function (r) { reasons[r] = (reasons[r] || 0) + 1; }); });
  Object.keys(reasons).sort().forEach(function (r) {
    var o = document.createElement("option");
    o.value = r;
    o.textContent = r + " (" + reasons[r] + ")";
    $("filter").appendChild(o);
  });
  CHARS.forEach(function (ch) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = ch;
    b.addEventListener("click", function () { insert(ch); });
    $("chars").appendChild(b);
  });
  $("source").textContent = "· " + R.source;
  $("filter").addEventListener("change", function () { rebuild(); });
  $("open-only").addEventListener("change", function () { rebuild(view[pos] && view[pos].id); });
  $("save").addEventListener("click", save);
  $("prev").addEventListener("click", function () { move(-1); });
  $("next").addEventListener("click", function () { move(1); });
  $("text").addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); save(); }
    else if (e.altKey && e.key === "ArrowLeft") { e.preventDefault(); move(-1); }
    else if (e.altKey && e.key === "ArrowRight") { e.preventDefault(); move(1); }
  });
  $("export").addEventListener("click", function () {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(answers, null, 1)], { type: "application/json" }));
    a.download = "numeral_answers.json";
    a.click();
  });
  $("load").addEventListener("change", function (e) {
    var f = e.target.files[0];
    if (!f) return;
    f.text().then(function (s) {
      var got = JSON.parse(s);
      Object.keys(got).forEach(function (k) { answers[k] = got[k]; });
      store();
      rebuild();
    });
  });
  rebuild();
})();
