/* ============================================================================
 * src/js/motion/heroSlides.js
 *
 * Crossfade for the home hero's two supplied banners.
 *
 * Deliberately tiny and dependency-free: it toggles one class and lets CSS
 * own the 900ms opacity transition. No animate() call, nothing measured, no
 * layout read — so it cannot contribute to the above-the-fold cost. The first
 * slide already carries `.is-active` in the HTML, so if this module never runs
 * (bundle blocked, throw upstream, no JS) the hero is still a finished,
 * correct-looking banner rather than an empty band.
 *
 * Three things it refuses to do:
 *   - run at all under `prefers-reduced-motion: reduce`, or ?noanim. An
 *     infinite decorative loop is the archetype of what that preference is
 *     asking to stop.
 *   - keep ticking while the tab is hidden. setInterval in a background tab
 *     burns wakeups and queues transitions nobody sees.
 *   - advance before the incoming image has decoded. Fading to a half-loaded
 *     JPEG shows a grey box; slide 2 is lazy, so on a slow connection it may
 *     genuinely not be ready at the six-second mark.
 * ========================================================================== */

import { motionOff, onMotionPreferenceChange } from './tokens.js';

const INTERVAL_MS = 6000;

const noop = () => {};

/* Module-scoped so a second initHeroSlides() replaces the first rather than
   stacking a second timer on the same element. */
let teardown = null;

export function initHeroSlides() {
  if (teardown) teardown();

  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return (teardown = noop);
  }

  const media = document.querySelector('[data-hero-slides]');
  if (!media) return (teardown = noop);

  const slides = Array.from(media.querySelectorAll('.home-hero__slide'));
  // One slide is a still, not a slideshow.
  if (slides.length < 2) return (teardown = noop);

  let index = Math.max(0, slides.findIndex((s) => s.classList.contains('is-active')));
  let timer = null;

  const show = (i) => {
    slides.forEach((s, n) => s.classList.toggle('is-active', n === i));
    index = i;
  };

  const advance = () => {
    const next = (index + 1) % slides.length;
    // `complete` covers cached and already-decoded; a lazy slide 2 on a slow
    // link is not. Skip this beat rather than fade to nothing — the next tick
    // will find it ready.
    if (!slides[next].complete || slides[next].naturalWidth === 0) return;
    show(next);
  };

  const stop = () => {
    if (timer !== null) {
      window.clearInterval(timer);
      timer = null;
    }
  };

  const start = () => {
    if (timer !== null || motionOff()) return;
    timer = window.setInterval(advance, INTERVAL_MS);
  };

  const onVisibility = () => (document.hidden ? stop() : start());

  // Mid-session flip to `reduce`: stop where it stands. Whichever slide is
  // showing stays; nothing rewinds.
  const unsub = onMotionPreferenceChange((reduced) => (reduced ? stop() : start()));

  document.addEventListener('visibilitychange', onVisibility);
  start();

  const cleanup = () => {
    stop();
    unsub();
    document.removeEventListener('visibilitychange', onVisibility);
    if (teardown === cleanup) teardown = null;
  };

  teardown = cleanup;
  return cleanup;
}
