/**
 * Wash4You — lightweight behavioral layer.
 * Styling lives in CSS; this file only does things CSS can't:
 * header scroll state, a skip-to-content link, and a branded
 * replacement for Next.js's default not-found boundary.
 */
(function () {
  'use strict';

  function onReady(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  function throttle(fn, limit) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        fn.apply(this, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  function initHeaderScroll() {
    const header = document.querySelector('header');
    if (!header) return;
    const onScroll = throttle(() => {
      header.classList.toggle('header-scrolled', window.scrollY > 24);
    }, 100);
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  function initSkipLink() {
    if (document.querySelector('.skip-link')) return;
    const link = document.createElement('a');
    link.href = '#main-content';
    link.className = 'skip-link';
    link.textContent = 'Skip to main content';
    link.style.cssText =
      'position:fixed;top:-40px;left:0;padding:10px 16px;background:#21B14B;' +
      'color:#fff;z-index:99999;transition:top 0.2s;font-size:14px;' +
      'text-decoration:none;border-radius:0 0 8px 0;';
    link.addEventListener('focus', () => (link.style.top = '0'));
    link.addEventListener('blur', () => (link.style.top = '-40px'));
    document.body.prepend(link);

    const main = document.getElementById('main-content') || document.querySelector('main');
    if (main && !main.id) main.id = 'main-content';
  }

  // React hydrates this app client-side. Never insert into or replace
  // nodes *inside* header/main/footer — React owns that subtree and a
  // structural mismatch makes it discard the server HTML and remount
  // from scratch, silently undoing the change. Appending new elements
  // directly to <body> (as siblings of header/main/footer) is the one
  // pattern that survives, matching how the skip-link above behaves.
  function enhanceNotFound() {
    const marker = document.querySelector('.next-error-h1');
    if (!marker) return;
    const main = document.querySelector('main');
    if (!main || document.querySelector('.w4u-404')) return;

    const custom = document.createElement('div');
    custom.className = 'w4u-404';
    custom.innerHTML =
      '<div class="w4u-404-card">' +
      '<img src="/images/mascot-wash4you.png" alt="" width="110" height="110" style="margin:0 auto 12px;display:block;" />' +
      '<div class="w4u-404-code">404</div>' +
      '<div class="w4u-404-tag">Claim not found</div>' +
      '<h1>This page didn’t survive the wash.</h1>' +
      '<p>The link is broken or the page has moved. Head back home, or find the service you were looking for.</p>' +
      '<div class="w4u-404-actions">' +
      '<a class="w4u-404-primary" href="/">Go to Homepage</a>' +
      '<a class="w4u-404-secondary" href="/services/">Browse Services</a>' +
      '</div>' +
      '</div>';
    main.insertAdjacentElement('afterend', custom);
  }

  var AREAS = [
    'Sector 29, Gurugram',
    'DLF Phase 3',
    'Cyber City',
    'Sushant Lok',
    'Golf Course Road',
    'Golf Course Extension',
    'Palam Vihar',
    'Sohna Road',
    'Somewhere else in Gurugram / Delhi NCR',
  ];

  // A floating WhatsApp quick-contact button, appended to <body> —
  // inspired by inline booking widgets on sites like Rinse, adapted to
  // how Wash4You actually takes bookings (a WhatsApp chat, not a live
  // reservation system) and kept outside React's tree for safety.
  function initQuickContact() {
    if (document.querySelector('.w4u-fab')) return;

    const fab = document.createElement('div');
    fab.className = 'w4u-fab';
    fab.innerHTML =
      '<button type="button" class="w4u-fab-toggle" aria-expanded="false" aria-controls="w4u-fab-panel">' +
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.4A10 10 0 1 0 12 2Zm5.4 14.3c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .1-3.3-.7-2.8-1.1-4.6-3.9-4.8-4.1-.1-.2-1.1-1.5-1.1-2.8 0-1.3.7-2 1-2.2.2-.2.5-.3.7-.3h.5c.2 0 .4 0 .6.5.2.6.7 1.9.8 2 .1.2.1.4 0 .6-.4.8-.8.8-.5 1.3.9 1.6 1.8 2.2 3.2 2.8.2.1.4.1.5-.1.2-.2.7-.8.9-1.1.2-.3.4-.2.6-.1.2.1 1.5.7 1.8.9.3.1.5.2.5.3.1.2.1.7-.1 1.3Z"/></svg>' +
      '<span class="w4u-fab-label">Chat on WhatsApp</span>' +
      '</button>' +
      '<div class="w4u-fab-panel" id="w4u-fab-panel" hidden>' +
      '<p class="w4u-fab-title">Check delivery to your area</p>' +
      '<select class="w4u-fab-select" aria-label="Select your area">' +
      '<option value="">Select your area…</option>' +
      AREAS.map(function (a) { return '<option>' + a + '</option>'; }).join('') +
      '</select>' +
      '<button type="button" class="w4u-fab-send">Start chat<span aria-hidden="true"> →</span></button>' +
      '</div>';
    document.body.appendChild(fab);

    const toggle = fab.querySelector('.w4u-fab-toggle');
    const panel = fab.querySelector('.w4u-fab-panel');
    const select = fab.querySelector('.w4u-fab-select');
    const send = fab.querySelector('.w4u-fab-send');

    toggle.addEventListener('click', function () {
      const open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      panel.hidden = open;
      if (!open) select.focus();
    });

    send.addEventListener('click', function () {
      const area = select.value;
      if (!area) {
        select.classList.add('w4u-quickcheck-invalid');
        select.focus();
        setTimeout(function () { select.classList.remove('w4u-quickcheck-invalid'); }, 900);
        return;
      }
      const msg = encodeURIComponent('Hi! I’d like to book a laundry pickup in ' + area + '.');
      window.open('https://wa.me/916367600500?text=' + msg, '_blank', 'noopener');
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        toggle.click();
        toggle.focus();
      }
    });
  }

  onReady(function () {
    initHeaderScroll();
    initSkipLink();
    enhanceNotFound();
    initQuickContact();
  });
})();
