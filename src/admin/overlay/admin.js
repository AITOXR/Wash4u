/* Wash4You admin overlay — click-to-edit, injected by the local admin server.
   Vanilla JS, no dependencies. Talks to /admin/api/*. */
(function () {
  "use strict";
  var CFG = window.__W4U_ADMIN__ || { user: "admin" };
  var dirty = new Map(); // binding -> new value

  // ---------- tiny DOM helpers ----------
  function h(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function api(path, body) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); });
  }

  // ---------- toast ----------
  var toastEl = h("div", "w4u-toast");
  function toast(msg, kind, sticky) {
    toastEl.textContent = msg;
    toastEl.className = "w4u-toast is-on" + (kind ? " w4u-toast--" + kind : "");
    if (!sticky) setTimeout(function () { toastEl.classList.remove("is-on"); }, 2600);
  }

  // A little woven care-label glyph — the wordmark's mark.
  var TAG_SVG = '<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">' +
    '<rect x="4" y="5" width="16" height="14" rx="2.6" fill="#0FB5A5"/>' +
    '<circle cx="8" cy="9" r="1.15" fill="#0C2340"/>' +
    '<rect x="11" y="8.2" width="6" height="1.6" rx=".8" fill="#0C2340" opacity=".55"/>' +
    '<rect x="7" y="13" width="10" height="1.6" rx=".8" fill="#0C2340" opacity=".32"/>' +
    '<rect x="7" y="15.6" width="7" height="1.6" rx=".8" fill="#0C2340" opacity=".32"/></svg>';

  // ---------- counter bar ----------
  var bar = h("div", "w4u-bar");
  var mark = h("div", "w4u-bar__mark");
  mark.innerHTML = TAG_SVG + "<span>Wash4You</span>";
  var editorTag = h("span", "w4u-bar__tag", "Editor");
  var hint = h("span", "w4u-bar__hint", "Click to edit");
  var spacer = h("div", "w4u-bar__spacer");
  var blogBtn = h("button", "w4u-btn", "Blog");
  var publishBtn = h("button", "w4u-btn w4u-btn--publish", "Publish");
  var logoutBtn = h("button", "w4u-btn", "Log out");
  var saveBtn = h("button", "w4u-btn w4u-btn--primary", "Save");
  saveBtn.disabled = true;
  bar.append(mark, editorTag, hint, spacer, blogBtn, saveBtn, publishBtn, logoutBtn);

  function refreshBar() {
    var n = dirty.size;
    saveBtn.disabled = n === 0;
    saveBtn.classList.toggle("is-dirty", n > 0);
    saveBtn.textContent = n ? "Save " + n : "Save";
    hint.textContent = n ? n + (n > 1 ? " unsaved edits" : " unsaved edit") : "Click to edit";
    hint.classList.toggle("is-dirty", n > 0);
  }

  // ---------- the field care-tag (names the field on hover / while editing) ----------
  var fieldTag = h("div", "w4u-tag");
  var GENERIC = { title:1, name:1, detail:1, label:1, value:1, text:1, excerpt:1,
    cta:1, button:1, subtitle:1, heading:1, headline:1, summary:1, q:1, a:1 };
  function humanize(binding) {
    var path = (binding.split(":")[1] || binding);
    var segs = path.split(".").filter(function (s) { return !/^\d+$/.test(s); });
    var last = segs[segs.length - 1] || path;
    var out = last;
    if (GENERIC[last] && segs.length > 1) out = segs[segs.length - 2].replace(/s$/, "") + " " + last;
    return out.replace(/_/g, " ").replace(/([a-z])([0-9])/g, "$1 $2").trim().toUpperCase();
  }
  function showTag(el, active) {
    var r = el.getBoundingClientRect();
    fieldTag.textContent = humanize(el.getAttribute("data-cms"));
    fieldTag.style.top = (r.top + window.scrollY - 27) + "px";
    fieldTag.style.left = (r.left + window.scrollX) + "px";
    fieldTag.classList.toggle("is-active", !!active);
    fieldTag.classList.add("is-on");
  }
  function hideTag() { fieldTag.classList.remove("is-on", "is-active"); }

  // ---------- text editing ----------
  function markDirty(el, binding, value) {
    dirty.set(binding, value);
    el.classList.add("w4u-dirty");
    refreshBar();
  }
  function activate(el) {
    if (el.isContentEditable) return;
    el.dataset.w4uOrig = el.innerText;
    el.setAttribute("contenteditable", "true");
    el.classList.add("w4u-active");
    showTag(el, true);
    el.focus();
    // caret to end
    var r = document.createRange();
    r.selectNodeContents(el); r.collapse(false);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
  }
  function commit(el) {
    if (!el.isContentEditable) return;
    el.removeAttribute("contenteditable");
    el.classList.remove("w4u-active");
    hideTag();
    var kind = el.getAttribute("data-cms-kind") || "text";
    var binding = el.getAttribute("data-cms");
    var orig = (el.dataset.w4uOrig || "").trim();
    var value = kind === "rich"
      ? el.innerHTML.trim()
      : el.innerText.replace(/\s*\n\s*/g, " ").trim();
    if (value !== orig) markDirty(el, binding, value);
  }

  function wireText(el) {
    el.addEventListener("mouseenter", function () { if (!el.isContentEditable) showTag(el, false); });
    el.addEventListener("mouseleave", function () { if (!el.isContentEditable) hideTag(); });
    el.addEventListener("click", function (e) {
      e.preventDefault();   // stop link navigation while editing
      e.stopPropagation();
      activate(el);
    });
    el.addEventListener("keydown", function (e) {
      var kind = el.getAttribute("data-cms-kind") || "text";
      if (e.key === "Enter" && kind !== "rich") { e.preventDefault(); el.blur(); }
      else if (e.key === "Escape") { el.innerText = el.dataset.w4uOrig || el.innerText; el.blur(); }
    });
    el.addEventListener("blur", function () { commit(el); });
  }

  // ---------- image editing ----------
  var picker = h("input");
  picker.type = "file";
  picker.accept = "image/*";
  picker.style.display = "none";
  var imgTarget = null;
  picker.addEventListener("change", function () {
    var file = picker.files && picker.files[0];
    if (file && imgTarget) uploadImage(imgTarget, file);
    picker.value = "";
  });
  function readDataURL(file) {
    return new Promise(function (res, rej) {
      var fr = new FileReader();
      fr.onload = function () { res(fr.result); };
      fr.onerror = rej;
      fr.readAsDataURL(file);
    });
  }
  function uploadImage(target, file) {
    toast("Uploading image…", null, true);
    readDataURL(file).then(function (dataUrl) {
      var payload = { name: file.name, dataUrl: dataUrl };
      if (target.hasAttribute("data-cms-file")) payload.file = target.getAttribute("data-cms-file");
      else payload.binding = target.getAttribute("data-cms");
      return api("/admin/api/upload", payload);
    }).then(function (r) {
      if (r.ok && r.data.ok) { toast("Image updated", "ok"); location.reload(); }
      else { toast(r.data.error || "Upload failed", "err"); if (r.data.detail) console.error(r.data.detail); }
    }).catch(function (err) { toast("Upload failed", "err"); console.error(err); });
  }

  var chip = h("button", "w4u-imgchip", "Swap image");
  var chipHideT = null;
  function showChip(img) {
    var rect = img.getBoundingClientRect();
    chip.style.top = (rect.top + window.scrollY + 8) + "px";
    chip.style.left = (rect.left + window.scrollX + 8) + "px";
    chip.classList.add("is-on");
    chip._target = img;
  }
  function hideChipSoon() { chipHideT = setTimeout(function () { chip.classList.remove("is-on"); }, 140); }
  function wireImage(img) {
    img.addEventListener("mouseenter", function () { clearTimeout(chipHideT); showChip(img); });
    img.addEventListener("mouseleave", hideChipSoon);
    img.addEventListener("click", function (e) {
      // Don't hijack images that are inside a link the user may want to follow,
      // unless it's the plain editable image case.
      e.preventDefault(); e.stopPropagation();
      imgTarget = img; picker.click();
    });
  }
  chip.addEventListener("mouseenter", function () { clearTimeout(chipHideT); });
  chip.addEventListener("mouseleave", hideChipSoon);
  chip.addEventListener("click", function () {
    if (chip._target) { imgTarget = chip._target; picker.click(); }
  });

  // ---------- save ----------
  saveBtn.addEventListener("click", function () {
    if (!dirty.size) return;
    var edits = [];
    dirty.forEach(function (value, binding) { edits.push({ binding: binding, value: value }); });
    saveBtn.disabled = true; saveBtn.textContent = "Saving…";
    api("/admin/api/save", { edits: edits }).then(function (r) {
      if (r.ok && r.data.ok) { toast("Saved — rebuilding…", "ok"); location.reload(); }
      else { toast(r.data.error || "Save failed", "err"); if (r.data.detail) console.error(r.data.detail); refreshBar(); }
    }).catch(function (err) { toast("Save failed", "err"); console.error(err); refreshBar(); });
  });

  // ---------- modal plumbing ----------
  var back = h("div", "w4u-modal-back");
  var modal = h("div", "w4u-modal");
  back.appendChild(modal);
  back.addEventListener("click", function (e) { if (e.target === back) closeModal(); });
  function openModal(title, bodyNode, footNode) {
    modal.innerHTML = "";
    var head = h("div", "w4u-modal__head");
    head.appendChild(h("h2", null, title));
    var x = h("button", "w4u-modal__x", "×");
    x.addEventListener("click", closeModal);
    head.appendChild(x);
    var body = h("div", "w4u-modal__body"); body.appendChild(bodyNode);
    modal.append(head, body);
    if (footNode) { var f = h("div", "w4u-modal__foot"); f.appendChild(footNode); modal.appendChild(f); }
    back.classList.add("is-on");
  }
  function closeModal() { back.classList.remove("is-on"); }

  function field(label, value, textarea) {
    var wrap = h("div", "w4u-field");
    wrap.appendChild(h("label", null, label));
    var input = h(textarea ? "textarea" : "input");
    if (!textarea) input.type = "text";
    input.value = value || "";
    wrap.appendChild(input);
    wrap._input = input;
    return wrap;
  }

  // ---------- blog manager ----------
  blogBtn.addEventListener("click", openBlog);
  function openBlog() {
    fetch("/admin/api/blog").then(function (r) { return r.json(); }).then(function (d) {
      renderBlog(d.posts || []);
    });
  }
  function renderBlog(posts) {
    var body = h("div");
    var addBtn = h("button", "w4u-mbtn w4u-mbtn--primary", "+ Add post");
    addBtn.style.marginBottom = "14px";
    addBtn.addEventListener("click", function () { editPost(null, posts); });
    body.appendChild(addBtn);
    posts.forEach(function (p, i) {
      var card = h("div", "w4u-post");
      var row = h("div", "w4u-post__row");
      var left = h("div");
      left.appendChild(h("div", "w4u-post__title", p.title || "(untitled)"));
      left.appendChild(h("div", "w4u-post__date", p.date || ""));
      var actions = h("div", "w4u-post__actions");
      var ed = h("button", "w4u-mbtn", "Edit");
      ed.addEventListener("click", function () { editPost(i, posts); });
      var del = h("button", "w4u-mbtn w4u-mbtn--danger", "Delete");
      del.addEventListener("click", function () {
        if (!confirm("Delete this post?")) return;
        api("/admin/api/blog", { action: "delete", index: i }).then(function (r) {
          if (r.ok && r.data.ok) { toast("Post deleted", "ok"); renderBlog(r.data.posts); }
          else toast(r.data.error || "Delete failed", "err");
        });
      });
      actions.append(ed, del);
      row.append(left, actions);
      card.appendChild(row);
      if (p.excerpt) card.appendChild(h("div", "w4u-post__excerpt", p.excerpt));
      body.appendChild(card);
    });
    openModal("Blog posts", body);
  }
  function editPost(index, posts) {
    var p = index == null ? { title: "", date: "", excerpt: "", url: "" } : posts[index];
    var body = h("div");
    var fTitle = field("Title", p.title);
    var fDate = field("Date (e.g. July 28, 2026)", p.date);
    var fUrl = field("Link URL", p.url);
    var fExcerpt = field("Excerpt", p.excerpt, true);
    body.append(fTitle, fDate, fUrl, fExcerpt);
    var save = h("button", "w4u-mbtn w4u-mbtn--primary", index == null ? "Add post" : "Save post");
    save.addEventListener("click", function () {
      var post = {
        title: fTitle._input.value.trim(),
        date: fDate._input.value.trim(),
        excerpt: fExcerpt._input.value.trim(),
        url: fUrl._input.value.trim(),
      };
      var payload = index == null
        ? { action: "create", post: post }
        : { action: "update", index: index, post: post };
      api("/admin/api/blog", payload).then(function (r) {
        if (r.ok && r.data.ok) { toast("Blog saved", "ok"); renderBlog(r.data.posts); }
        else toast(r.data.error || "Save failed", "err");
      });
    });
    var cancel = h("button", "w4u-mbtn", "Back");
    cancel.addEventListener("click", function () { renderBlog(posts); });
    var foot = h("div"); foot.append(cancel, save);
    openModal(index == null ? "Add blog post" : "Edit blog post", body, foot);
  }

  // ---------- publish ----------
  publishBtn.addEventListener("click", function () {
    if (dirty.size && !confirm("You have unsaved edits that won't be published. Save them first?\n\nOK = continue to Publish anyway, Cancel = go back.")) return;
    var body = h("div");
    var fMsg = field("Commit message", "Update site content via admin");
    body.appendChild(fMsg);
    var commitWrap = h("label", "w4u-check");
    var commitCb = h("input"); commitCb.type = "checkbox"; commitCb.checked = true;
    commitWrap.append(commitCb, h("span", null, "Commit the rebuilt site to git (recommended)"));
    var pushWrap = h("label", "w4u-check"); pushWrap.style.marginTop = "12px";
    var pushCb = h("input"); pushCb.type = "checkbox";
    pushWrap.append(pushCb, h("span", null, "Push to the live public site (git push)"));
    var warn = h("div", "w4u-warn", "Push makes your changes public on wash4you.in's deploy target. Leave off to review the commit first.");
    body.append(commitWrap, pushWrap, warn);
    var go = h("button", "w4u-mbtn w4u-mbtn--primary", "Publish");
    go.addEventListener("click", function () {
      go.disabled = true; go.textContent = "Publishing…";
      api("/admin/api/publish", {
        message: fMsg._input.value.trim() || "Update site content via admin",
        commit: commitCb.checked, push: pushCb.checked,
      }).then(function (r) {
        var steps = (r.data.steps || []).join("\n");
        if (r.data.ok) { toast("Published ✓", "ok"); }
        else { toast("Publish finished with issues — see dialog", "err", true); }
        alert((r.data.ok ? "Publish complete:\n\n" : "Publish result:\n\n") + steps + (r.data.detail ? "\n\n" + r.data.detail : ""));
        closeModal();
      }).catch(function (err) { toast("Publish failed", "err"); console.error(err); go.disabled = false; go.textContent = "Publish"; });
    });
    var cancel = h("button", "w4u-mbtn", "Cancel");
    cancel.addEventListener("click", closeModal);
    var foot = h("div"); foot.append(cancel, go);
    openModal("Publish changes", body, foot);
  });

  // ---------- logout ----------
  logoutBtn.addEventListener("click", function () {
    if (dirty.size && !confirm("You have unsaved changes. Log out anyway?")) return;
    window.location = "/admin/logout";
  });

  // ---------- unsaved guard ----------
  window.addEventListener("beforeunload", function (e) {
    if (dirty.size) { e.preventDefault(); e.returnValue = ""; }
  });

  // ---------- boot ----------
  function boot() {
    document.body.appendChild(bar);
    document.body.appendChild(toastEl);
    document.body.appendChild(back);
    document.body.appendChild(picker);
    document.body.appendChild(chip);
    document.body.appendChild(fieldTag);
    document.querySelectorAll("[data-cms]").forEach(wireText);
    document.querySelectorAll("[data-cms-file], [data-cms-kind='image']").forEach(wireImage);
    refreshBar();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
