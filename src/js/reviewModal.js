/* ============================================================================
 * src/js/reviewModal.js
 *
 * "Read more" for the customer reviews.
 *
 * ui.css clamps .review__quote to three lines under `.js`. This module:
 *   1. measures which quotes are actually overflowing and reveals the
 *      "Read more" button only on those,
 *   2. opens the full review in a native <dialog> when the button or
 *      anywhere on a clamped card is activated.
 *
 * Why measure instead of counting characters in the template: whether three
 * lines is enough depends on the rendered width, the font that actually
 * loaded, and the language. A server-side length threshold shows the button
 * on cards that fit and hides it on cards that don't.
 *
 * The dialog is built ONCE and reused, and its content is read from the card
 * that was clicked — no duplicated markup, no data-* attribute carrying an
 * escaped copy of every quote.
 * ========================================================================== */

const SELECTOR = '.review';

let teardown = null;
let dialog = null;

/* One dialog for the whole page, created on first open. */
function ensureDialog() {
  if (dialog) return dialog;

  dialog = document.createElement('dialog');
  dialog.className = 'review-dialog';
  dialog.innerHTML =
    '<button type="button" class="review-dialog__close" aria-label="Close review">&times;</button>' +
    '<div class="review-dialog__body"></div>';

  dialog.querySelector('.review-dialog__close').addEventListener('click', () => dialog.close());

  // Click on the backdrop closes. The dialog element's own box covers the
  // card area, so a click landing on the element itself means the backdrop.
  dialog.addEventListener('click', (e) => {
    if (e.target === dialog) dialog.close();
  });

  // Removing the iframe is what STOPS playback — pausing is not enough, and
  // a closed <dialog> keeps its children alive and audible.
  dialog.addEventListener('close', () => {
    dialog.querySelector('.review-dialog__body').replaceChildren();
    dialog.classList.remove('review-dialog--video');
  });

  document.body.appendChild(dialog);
  return dialog;
}

/* Swap the poster facade for the real player. Built only on click, so a
   visitor who never presses play never touches youtube.com. */
function openVideo(card) {
  const id = card.getAttribute('data-video-id');
  if (!id) return;

  const d = ensureDialog();
  const body = d.querySelector('.review-dialog__body');
  d.classList.add('review-dialog--video');

  const frame = document.createElement('div');
  frame.className = 'review-dialog__video';

  const iframe = document.createElement('iframe');
  // youtube-nocookie: no tracking cookie is set for a visitor who presses
  // play but never signs in. playsinline stops iOS hijacking to fullscreen.
  iframe.src =
    'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) +
    '?autoplay=1&rel=0&playsinline=1&modestbranding=1';
  iframe.title = card.getAttribute('data-video-title') || 'Customer video';
  iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share';
  iframe.allowFullscreen = true;
  iframe.referrerPolicy = 'strict-origin-when-cross-origin';

  frame.appendChild(iframe);
  body.replaceChildren(frame);

  if (typeof d.showModal === 'function') d.showModal();
  else window.open('https://www.youtube.com/watch?v=' + id, '_blank', 'noopener');
}

function openFor(card) {
  const d = ensureDialog();
  const body = d.querySelector('.review-dialog__body');

  // Clone the card's own nodes: stars, the full quote (the element holds the
  // complete text — the clamp only hid it visually) and the attribution.
  body.replaceChildren();
  ['.review__stars', '.review__quote', '.review__who'].forEach((sel) => {
    const part = card.querySelector(sel);
    if (part) body.appendChild(part.cloneNode(true));
  });

  if (typeof d.showModal === 'function') {
    d.showModal();
  } else {
    // No <dialog> support: fall back to un-clamping the card in place rather
    // than trapping the text behind a control that cannot open.
    card.classList.remove('is-clamped');
    card.querySelector('.review__quote').style.webkitLineClamp = 'unset';
  }
}

/* A quote is clamped when its content is taller than its box. 1px of slack
   absorbs sub-pixel line-height rounding, which otherwise reports a
   one-line quote as overflowing on some zoom levels. */
const isOverflowing = (el) => el.scrollHeight > el.clientHeight + 1;

export function initReviewModal() {
  if (teardown) teardown();

  if (typeof document === 'undefined') return (teardown = () => {});

  const cards = Array.from(document.querySelectorAll(SELECTOR));
  if (!cards.length) return (teardown = () => {});

  const sync = () => {
    cards.forEach((card) => {
      // Video cards carry neither a quote nor a Read-more button.
      const quote = card.querySelector('.review__quote');
      const btn = card.querySelector('.review__more');
      if (!quote || !btn) return;
      const clamped = isOverflowing(quote);
      btn.hidden = !clamped;
      card.classList.toggle('is-clamped', clamped);
    });
  };

  // Fonts change line-breaking, so a measurement taken before the webfont
  // swaps in can be wrong in both directions.
  sync();
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(sync).catch(() => {});
  }

  const onClick = (e) => {
    const card = e.target.closest(SELECTOR);
    if (!card) return;

    // Video cards open the player; they have no quote to clamp.
    if (card.classList.contains('review--video')) {
      e.preventDefault();
      openVideo(card);
      return;
    }

    if (!card.classList.contains('is-clamped')) return;
    // Let real links and other controls inside a card keep working.
    if (e.target.closest('a, button:not(.review__more)')) return;
    e.preventDefault();
    openFor(card);
  };

  // Keyboard needs no separate handler: activating the <button> fires a
  // click, which this same delegated listener receives.
  document.addEventListener('click', onClick);

  // Re-measure on resize: the rail's cards change width at every breakpoint,
  // and a quote that needed four lines at 320px may fit three at 400px.
  let raf = 0;
  const onResize = () => {
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(sync);
  };
  window.addEventListener('resize', onResize);

  const cleanup = () => {
    document.removeEventListener('click', onClick);
    window.removeEventListener('resize', onResize);
    if (raf) cancelAnimationFrame(raf);
    if (teardown === cleanup) teardown = null;
  };

  teardown = cleanup;
  return cleanup;
}
