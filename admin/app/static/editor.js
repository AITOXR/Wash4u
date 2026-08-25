/* Wash4You WYSIWYG editor overlay. "The website is the editor" — this
   renders on top of the REAL live page (see templates/base.html's
   edit_mode block) and patches individual fields back to the server.
   Vanilla JS + SortableJS (loaded via CDN, see base.html) — no build step,
   consistent with the rest of this admin. */
(function () {
  "use strict";
  var CFG = window.__W4U_EDITOR__ || {};
  if (!CFG.canEdit) { wireViewOnly(); return; }

  function h(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function api(method, path, body) {
    var opts = { method: method, headers: {} };
    if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
    return fetch(path, opts).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); });
  }

  // ---------------------------------------------------------------- toast
  var toastEl = h("div", "w4u-toast");
  function toast(msg, kind) {
    toastEl.textContent = msg;
    toastEl.className = "w4u-toast is-on" + (kind ? " w4u-toast--" + kind : "");
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(function () { toastEl.classList.remove("is-on"); }, 2400);
  }

  // ------------------------------------------------------------- top bar
  var bar = h("div", "w4u-bar");
  var menuBtn = h("button", "w4u-bar__menu-btn", "&#9776; Menu");
  var title = h("span", "w4u-bar__title", CFG.pageTitle || "");
  var spacer = h("div", "w4u-bar__spacer");
  var devices = h("div", "w4u-bar__devices");
  ["desktop", "tablet", "phone"].forEach(function (d) {
    var b = h("button", "w4u-bar__device" + (d === "desktop" ? " is-active" : ""), d === "desktop" ? "&#128421;" : d === "tablet" ? "&#128432;" : "&#128241;");
    b.title = d.charAt(0).toUpperCase() + d.slice(1);
    b.addEventListener("click", function () { setDevice(d, b); });
    devices.appendChild(b);
  });
  var pending = h("span", "w4u-bar__pending" + (CFG.pendingCount ? "" : " is-zero"), (CFG.pendingCount || 0) + " unpublished");
  var publishBtn = h("a", "w4u-bar__btn w4u-bar__btn--primary", "Publish");
  publishBtn.href = "/admin/publish";
  bar.append(menuBtn, title, spacer, devices, pending, publishBtn);

  // -------------------------------------------------------------- menu
  var menu = h("div", "w4u-menu");
  menu.innerHTML =
    '<div class="w4u-menu__section">Content</div>' +
    '<a href="/admin/pages">Pages</a>' +
    '<a href="/admin/products">Products</a>' +
    '<a href="/admin/blog">Blog</a>' +
    '<a href="/admin/media">Media</a>' +
    '<div class="w4u-menu__section">Business</div>' +
    '<a href="/admin/dashboard">Dashboard</a>' +
    '<a href="/admin/orders">Orders</a>' +
    '<a href="/admin/crm">Customers</a>' +
    '<a href="/admin/leads">Leads</a>' +
    '<div class="w4u-menu__section">This page</div>' +
    '<button type="button" class="w4u-menu__item" data-action="page-settings">Page settings</button>' +
    '<button type="button" class="w4u-menu__item" data-action="revisions">Revision history</button>' +
    '<div class="w4u-menu__section">Account</div>' +
    '<a href="/admin/settings">Settings</a>' +
    '<a href="/admin/logout" data-nav="logout">Log out</a>';
  menuBtn.addEventListener("click", function () { menu.classList.toggle("is-open"); });
  menu.addEventListener("click", function (e) {
    var item = e.target.closest("[data-action]");
    if (!item) return;
    if (item.dataset.action === "revisions" && CFG.pageId) window.location = "/admin/pages/" + CFG.pageId + "/revisions";
    if (item.dataset.action === "page-settings") openPageSettings();
  });
  document.addEventListener("click", function (e) {
    if (menu.classList.contains("is-open") && !menu.contains(e.target) && e.target !== menuBtn) menu.classList.remove("is-open");
  });

  // --------------------------------------------------------- device preview
  // Toggling to tablet/phone re-renders THIS SAME editable page inside a
  // width-constrained iframe rather than trying to fake a viewport with
  // CSS — the header/offer-strip/etc. use position:fixed relative to the
  // real viewport, so only an actual separate browsing context reproduces
  // narrow-screen layout correctly. Editing still works fully inside it;
  // it's the exact same page and the exact same API calls.
  var deviceOverlay = null;
  function setDevice(mode, btnEl) {
    devices.querySelectorAll(".w4u-bar__device").forEach(function (b) { b.classList.remove("is-active"); });
    btnEl.classList.add("is-active");
    if (deviceOverlay) { deviceOverlay.remove(); deviceOverlay = null; }
    if (mode === "desktop") return;
    var width = mode === "tablet" ? "48rem" : "23.4rem";
    deviceOverlay = h("div");
    deviceOverlay.style.cssText = "position:fixed;inset:" + "var(--w4u-bar-h) 0 0 0;z-index:2147482990;background:rgba(9,20,42,.35);display:flex;align-items:flex-start;justify-content:center;padding:2rem;overflow:auto";
    var frame = document.createElement("iframe");
    frame.src = location.pathname;
    frame.style.cssText = "width:" + width + ";height:calc(100vh - var(--w4u-bar-h) - 4rem);border:0;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.4);background:#fff";
    deviceOverlay.appendChild(frame);
    deviceOverlay.addEventListener("click", function (e) { if (e.target === deviceOverlay) { deviceOverlay.remove(); deviceOverlay = null; devices.querySelector('[title="Desktop"]').classList.add("is-active"); btnEl.classList.remove("is-active"); } });
    document.body.appendChild(deviceOverlay);
  }

  // -------------------------------------------------------- field tag + toolbar
  var fieldTag = h("div", "w4u-field-tag");
  function humanize(key) { return key.replace(/_/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); }); }
  function showTag(el) {
    var r = el.getBoundingClientRect();
    fieldTag.textContent = humanize(el.getAttribute("data-field"));
    fieldTag.style.top = (r.top + window.scrollY - 24) + "px";
    fieldTag.style.left = (r.left + window.scrollX) + "px";
    fieldTag.classList.add("is-on");
  }
  function hideTag() { fieldTag.classList.remove("is-on"); }

  var textToolbar = h("div", "w4u-text-toolbar", '<button data-cmd="bold"><b>B</b></button><button data-cmd="italic"><i>i</i></button><button data-cmd="createLink">&#128279;</button>');
  textToolbar.addEventListener("mousedown", function (e) {
    var btn = e.target.closest("button");
    if (!btn) return;
    e.preventDefault();
    if (btn.dataset.cmd === "createLink") {
      var url = prompt("Link to:");
      if (url) document.execCommand("createLink", false, url);
    } else {
      document.execCommand(btn.dataset.cmd, false, null);
    }
  });
  function showToolbar(el) {
    var r = el.getBoundingClientRect();
    textToolbar.style.top = (r.top + window.scrollY - 40) + "px";
    textToolbar.style.left = r.left + window.scrollX + "px";
    textToolbar.classList.add("is-on");
  }
  function hideToolbar() { textToolbar.classList.remove("is-on"); }

  // ------------------------------------------------------------ undo stack
  // Covers field-level edits (the overwhelming majority of what Ctrl+Z is
  // used for while writing copy). Structural changes — a deleted or
  // reordered section — are NOT on this stack; Revision History (menu ->
  // "Revision history") is the safety net for those instead of a second,
  // parallel undo system.
  var undoStack = [], redoStack = [];
  function pushUndo(sectionId, field, prevValue) { undoStack.push({ sectionId: sectionId, field: field, value: prevValue }); redoStack.length = 0; }
  function performUndo() {
    var step = undoStack.pop();
    if (!step) return;
    var el = document.querySelector('[data-section-id="' + step.sectionId + '"] [data-field="' + step.field.split(".")[0] + '"]');
    redoStack.push({ sectionId: step.sectionId, field: step.field, value: getFieldCurrentText(step.sectionId, step.field) });
    setFieldValue(step.sectionId, step.field, step.value);
    api("POST", "/admin/api/sections/" + step.sectionId + "/field", { field: step.field, value: step.value });
  }
  function performRedo() {
    var step = redoStack.pop();
    if (!step) return;
    undoStack.push({ sectionId: step.sectionId, field: step.field, value: getFieldCurrentText(step.sectionId, step.field) });
    setFieldValue(step.sectionId, step.field, step.value);
    api("POST", "/admin/api/sections/" + step.sectionId + "/field", { field: step.field, value: step.value });
  }
  function getFieldCurrentText(sectionId, field) {
    var el = fieldEl(sectionId, field);
    return el ? el.innerText : "";
  }
  function setFieldValue(sectionId, field, value) {
    var el = fieldEl(sectionId, field);
    if (el) el.innerText = value;
  }
  function fieldEl(sectionId, field) {
    var top = field.split(".")[0];
    return document.querySelector('[data-section-id="' + sectionId + '"] [data-field="' + top + '"]');
  }
  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z") {
      e.preventDefault();
      if (e.shiftKey) performRedo(); else performUndo();
    }
  });

  // ------------------------------------------------------------- text editing
  function fieldPath(el) {
    var repItem = el.closest("[data-repeater-item]");
    if (repItem) {
      var repContainer = el.closest("[data-repeater]");
      return repContainer.getAttribute("data-repeater") + "." + repItem.getAttribute("data-repeater-index") + "." + el.getAttribute("data-field");
    }
    return el.getAttribute("data-field");
  }
  function sectionIdOf(el) { var s = el.closest("[data-section-id]"); return s ? s.getAttribute("data-section-id") : null; }

  function activateText(el) {
    if (el.isContentEditable) return;
    el.dataset.w4uOrig = el.innerText;
    el.setAttribute("contenteditable", "true");
    el.classList.add("w4u-active");
    showTag(el);
    if (el.getAttribute("data-field-kind") === "richtext") showToolbar(el);
    el.focus();
    var r = document.createRange(); r.selectNodeContents(el); r.collapse(false);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
  }
  function commitText(el) {
    if (!el.isContentEditable) return;
    el.removeAttribute("contenteditable");
    el.classList.remove("w4u-active");
    hideTag(); hideToolbar();
    var value = el.innerText.replace(/\s*\n\s*/g, " ").trim();
    var orig = (el.dataset.w4uOrig || "").trim();
    if (value === orig) return;
    var sectionId = sectionIdOf(el), field = fieldPath(el);
    pushUndo(sectionId, field, orig);
    el.classList.add("w4u-dirty");
    api("POST", "/admin/api/sections/" + sectionId + "/field", { field: field, value: value }).then(function (r) {
      if (r.ok && r.data.ok) { toast("Saved", "ok"); bumpPending(); } else toast("Save failed", "err");
    });
  }
  function wireText(el) {
    el.addEventListener("mouseenter", function () { if (!el.isContentEditable) showTag(el); });
    el.addEventListener("mouseleave", function () { if (!el.isContentEditable) hideTag(); });
    el.addEventListener("click", function (e) { e.stopPropagation(); activateText(el); });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && el.getAttribute("data-field-kind") !== "richtext") { e.preventDefault(); el.blur(); }
      else if (e.key === "Escape") { el.innerText = el.dataset.w4uOrig || el.innerText; el.blur(); }
    });
    el.addEventListener("blur", function () { commitText(el); });
  }

  function bumpPending() {
    var n = parseInt(pending.textContent, 10) || 0;
    // Only bump once per page load's worth of edits isn't tracked precisely
    // here — the exact count is re-read from the server on next full nav;
    // this just flips the "something changed" indicator on immediately.
    pending.classList.remove("is-zero");
  }

  // ----------------------------------------------------------- image swap
  var picker = h("input"); picker.type = "file"; picker.accept = "image/*"; picker.style.display = "none";
  var imgTarget = null;
  picker.addEventListener("change", function () {
    var file = picker.files && picker.files[0];
    if (file && imgTarget) uploadImage(imgTarget, file);
    picker.value = "";
  });
  function uploadImage(el, file) {
    toast("Uploading…");
    var fd = new FormData(); fd.append("file", file);
    fetch("/admin/api/upload", { method: "POST", body: fd }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok) { toast(d.error || "Upload failed", "err"); return; }
      var img = el.tagName === "IMG" ? el : el.querySelector("img");
      if (img) img.src = (img.src.split("/assets/")[0] || "") + "/assets/" + d.url;
      var sectionId = sectionIdOf(el), field = fieldPath(el);
      api("POST", "/admin/api/sections/" + sectionId + "/field", { field: field, value: d.url }).then(function (r2) {
        toast(r2.ok ? "Photo updated" : "Saved image but couldn't update the page — try refreshing", r2.ok ? "ok" : "err");
        bumpPending();
      });
    }).catch(function () { toast("Upload failed", "err"); });
  }
  var imgChip = h("button", "w4u-imgchip", "Swap image");
  var chipHideT;
  function wireImage(el) {
    var target = el.tagName === "IMG" ? el : el;
    el.addEventListener("mouseenter", function () { clearTimeout(chipHideT); var r = el.getBoundingClientRect(); imgChip.style.top = (r.top + window.scrollY + 8) + "px"; imgChip.style.left = (r.left + window.scrollX + 8) + "px"; imgChip.classList.add("is-on"); imgChip._target = el; });
    el.addEventListener("mouseleave", function () { chipHideT = setTimeout(function () { imgChip.classList.remove("is-on"); }, 150); });
    el.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); imgTarget = el; picker.click(); });
  }
  imgChip.addEventListener("mouseenter", function () { clearTimeout(chipHideT); });
  imgChip.addEventListener("mouseleave", function () { chipHideT = setTimeout(function () { imgChip.classList.remove("is-on"); }, 150); });
  imgChip.addEventListener("click", function () { if (imgChip._target) { imgTarget = imgChip._target; picker.click(); } });

  // ---------------------------------------------------------- button fields
  function wireButton(el) {
    el.addEventListener("click", function (e) {
      e.preventDefault(); e.stopPropagation();
      var sectionId = sectionIdOf(el), field = fieldPath(el);
      var newLabel = prompt("Button text:", el.innerText.trim());
      if (newLabel == null) return;
      el.innerText = newLabel;
      api("POST", "/admin/api/sections/" + sectionId + "/field", { field: field, value: newLabel }).then(function (r) {
        toast(r.ok ? "Saved" : "Save failed", r.ok ? "ok" : "err");
      });
    });
  }

  // --------------------------------------------------------- repeater add/remove
  function wireRepeaterControls(root) {
    root.querySelectorAll("[data-repeater-add]").forEach(function (btn) {
      if (btn._wired) return; btn._wired = true;
      btn.addEventListener("click", function () {
        var container = btn.closest("[data-repeater]");
        var section = btn.closest("[data-section-id]");
        var field = container.getAttribute("data-repeater");
        var sectionId = section.getAttribute("data-section-id");
        api("POST", "/admin/api/sections/" + sectionId + "/repeater/add", { field: field }).then(function (r) {
          if (r.ok && r.data.ok) refreshSection(sectionId); else toast("Couldn't add", "err");
        });
      });
    });
    root.querySelectorAll("[data-repeater-item] .w4u-rep-remove").forEach(function (btn) {
      if (btn._wired) return; btn._wired = true;
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        var item = btn.closest("[data-repeater-item]");
        var container = item.closest("[data-repeater]");
        var section = btn.closest("[data-section-id]");
        var field = container.getAttribute("data-repeater");
        var index = parseInt(item.getAttribute("data-repeater-index"), 10);
        var sectionId = section.getAttribute("data-section-id");
        if (!confirm("Remove this item?")) return;
        api("POST", "/admin/api/sections/" + sectionId + "/repeater/remove", { field: field, index: index }).then(function (r) {
          if (r.ok && r.data.ok) refreshSection(sectionId); else toast("Couldn't remove", "err");
        });
      });
    });
  }
  function refreshSection(sectionId) {
    api("GET", "/admin/api/sections/" + sectionId + "/render").then(function (r) {
      if (!r.ok || !r.data.ok) { toast("Refresh failed", "err"); return; }
      var el = document.querySelector('.w4u-section[data-section-id="' + sectionId + '"]');
      if (!el) return;
      var tmp = document.createElement("div"); tmp.innerHTML = r.data.html;
      var fresh = tmp.firstElementChild;
      el.replaceWith(fresh);
      wireAll(fresh);
      toast("Updated", "ok");
    });
  }

  // ------------------------------------------------------ section toolbar
  function buildSectionToolbar(sectionEl) {
    if (sectionEl.querySelector(":scope > .w4u-section-toolbar")) return;
    var tb = h("div", "w4u-section-toolbar");
    tb.innerHTML =
      '<button class="w4u-drag-handle" title="Drag to reorder">&#10021;</button>' +
      '<button data-act="duplicate" title="Duplicate">&#8862;</button>' +
      '<button data-act="hide" title="Hide/show">&#128065;</button>' +
      '<button data-act="delete" title="Delete">&#128465;</button>';
    tb.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-act]");
      if (!btn) return;
      var sectionId = sectionEl.getAttribute("data-section-id");
      if (btn.dataset.act === "duplicate") {
        api("POST", "/admin/api/sections/" + sectionId + "/duplicate").then(function (r) {
          if (r.ok && r.data.ok) { sectionEl.insertAdjacentHTML("afterend", r.data.html); wireAll(sectionEl.nextElementSibling); toast("Duplicated", "ok"); }
        });
      } else if (btn.dataset.act === "hide") {
        api("POST", "/admin/api/sections/" + sectionId + "/toggle-visible").then(function (r) {
          if (r.ok) { sectionEl.classList.toggle("w4u-section--hidden", !r.data.visible); toast(r.data.visible ? "Section shown" : "Section hidden", "ok"); }
        });
      } else if (btn.dataset.act === "delete") {
        if (!confirm("Delete this section? You can restore it from Revision History afterwards.")) return;
        api("POST", "/admin/api/sections/" + sectionId + "/delete").then(function (r) {
          if (r.ok && r.data.ok) { sectionEl.remove(); toast("Deleted — restorable from Revision History", "ok"); }
        });
      }
    });
    sectionEl.style.position = sectionEl.style.position || "relative";
    sectionEl.appendChild(tb);
  }

  // -------------------------------------------------------- drag reorder
  function wireSortable() {
    var containers = {};
    document.querySelectorAll(".w4u-section").forEach(function (el) {
      var parent = el.parentElement;
      if (!containers[parent === document.body ? "body" : "x"]) containers.list = containers.list || [];
    });
    // All .w4u-section elements share one parent (main > the loop output) —
    // find it once.
    var first = document.querySelector(".w4u-section");
    if (!first || typeof Sortable === "undefined") return;
    var parent = first.parentElement;
    if (parent._w4uSortable) return;
    parent._w4uSortable = new Sortable(parent, {
      handle: ".w4u-drag-handle",
      draggable: ".w4u-section",
      filter: ".w4u-insert",
      ghostClass: "w4u-sortable-ghost",
      chosenClass: "w4u-sortable-chosen",
      animation: 150,
      onEnd: function () {
        var order = Array.from(parent.querySelectorAll(".w4u-section")).map(function (el) { return parseInt(el.getAttribute("data-section-id"), 10); });
        api("POST", "/admin/api/pages/" + CFG.pageId + "/sections/reorder", { order: order }).then(function (r) {
          toast(r.ok ? "Reordered" : "Reorder failed", r.ok ? "ok" : "err");
        });
      },
    });
  }

  // ---------------------------------------------------- "+" insert picker
  var pickerBack = h("div", "w4u-picker-back");
  var pickerBox = h("div", "w4u-picker");
  pickerBack.appendChild(pickerBox);
  pickerBack.addEventListener("click", function (e) { if (e.target === pickerBack) pickerBack.classList.remove("is-on"); });
  var currentInsertAt = 0;
  function openPicker(insertAt) {
    currentInsertAt = insertAt;
    api("GET", CFG.sectionTypesUrl || "/admin/api/section-types").then(function (r) {
      if (!r.ok) return;
      var grid = h("div", "w4u-picker__grid");
      r.data.forEach(function (t) {
        var card = h("div", "w4u-picker__card");
        card.innerHTML = '<div class="w4u-picker__card-icon">&#9645;</div><div class="w4u-picker__card-label">' + t.label + "</div>";
        card.title = t.description || "";
        card.addEventListener("click", function () {
          pickerBack.classList.remove("is-on");
          api("POST", "/admin/api/pages/" + CFG.pageId + "/sections/create", { type: t.type, index: currentInsertAt }).then(function (r2) {
            if (!r2.ok || !r2.data.ok) { toast("Couldn't add section", "err"); return; }
            var insertPoints = document.querySelectorAll(".w4u-insert");
            var target = insertPoints[currentInsertAt];
            target.insertAdjacentHTML("afterend", r2.data.html);
            var newSection = target.nextElementSibling;
            wireAll(newSection);
            renumberInsertPoints();
            newSection.scrollIntoView({ behavior: "smooth", block: "center" });
            toast("Section added", "ok");
          });
        });
        grid.appendChild(card);
      });
      pickerBox.innerHTML = '<div class="w4u-picker__head"><h2>Add a section</h2><button class="w4u-modal__x" style="border:0;background:none;font-size:22px;cursor:pointer">&times;</button></div>';
      pickerBox.querySelector("button").addEventListener("click", function () { pickerBack.classList.remove("is-on"); });
      pickerBox.appendChild(grid);
      pickerBack.classList.add("is-on");
    });
  }
  function wireInsertPoints(root) {
    (root || document).querySelectorAll(".w4u-insert").forEach(function (ip) {
      if (ip._wired) return; ip._wired = true;
      var btn = h("button", "w4u-insert__btn", "+");
      btn.type = "button";
      btn.addEventListener("click", function () { openPicker(parseInt(ip.getAttribute("data-insert-at"), 10)); });
      ip.appendChild(btn);
    });
  }
  function renumberInsertPoints() {
    document.querySelectorAll(".w4u-insert").forEach(function (ip, i) { ip.setAttribute("data-insert-at", i); });
  }

  // ------------------------------------------------------------- page settings
  function openPageSettings() {
    window.location = "/admin/pages"; // full settings form — a rare enough action that a normal page is fine here.
  }

  // ----------------------------------------------------------------- boot
  function wireAll(root) {
    root = root || document;
    root.querySelectorAll('[data-field]:not([data-field-kind])').forEach(function (el) { if (!el._wired) { el._wired = true; wireText(el); } });
    root.querySelectorAll('[data-field-kind="richtext"]').forEach(function (el) { if (!el._wired) { el._wired = true; wireText(el); } });
    root.querySelectorAll('[data-field-kind="image"]').forEach(function (el) { if (!el._wired) { el._wired = true; wireImage(el); } });
    root.querySelectorAll('[data-field-kind="button"]').forEach(function (el) { if (!el._wired) { el._wired = true; wireButton(el); } });
    (root.matches && root.matches(".w4u-section") ? [root] : root.querySelectorAll(".w4u-section")).forEach(function (el) { buildSectionToolbar(el); });
    wireRepeaterControls(root);
    wireInsertPoints(root);
  }

  function boot() {
    document.body.append(bar, menu, toastEl, fieldTag, textToolbar, imgChip, picker, pickerBack);
    wireAll(document);
    wireSortable();
    window.addEventListener("beforeunload", function () { /* every change is already persisted server-side on commit — nothing to warn about */ });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  function wireViewOnly() {
    document.addEventListener("DOMContentLoaded", function () {
      var note = document.createElement("div");
      note.textContent = "View only — ask an owner or editor for edit access.";
      note.style.cssText = "position:fixed;top:0;left:0;right:0;background:#0C2340;color:#fff;padding:10px;text-align:center;z-index:999999;font-family:sans-serif;font-size:13px";
      document.body.prepend(note);
    });
  }
})();
