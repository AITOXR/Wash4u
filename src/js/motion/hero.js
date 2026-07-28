/* ============================================================================
 * src/js/motion/hero.js
 *
 * Guard for the above-the-fold cascade. Contains ZERO animate() calls, and
 * imports nothing from motion — deliberately.
 *
 * The bundle is loaded `defer` (base.html:222), so it executes after HTML parse
 * and after the five render-blocking stylesheets — typically 100-600ms after
 * first paint on 4G. The headline (page-home.html:41) is
 * `<h1 class="display-xl reveal reveal-delay-1">`, and `.js .reveal` is
 * opacity:0, so anything JS-driven hides the H1 until a deferred bundle boots.
 * A CSS keyframe starts animating at first paint and needs no bundle. Motion
 * cannot beat that, so animations.css owns the hero cascade — `hero-in`, four
 * beats at 90ms (the care note rides with the H1 on beat 0), settled at 770ms —
 * and this module owns only its off switch.
 *
 * The single class it writes, `hero--settled`, is matched by the LAST hero rule
 * in animations.css, so it wins on source order over the per-beat delay rules
 * at equal specificity. It only ever ADDS visibility (animation:none, opacity:1,
 * transform:none), so writing it after first paint can never cause a flash —
 * including on `.hero__proof`, the preloaded LCP candidate, which is already at
 * opacity 1 and is unaffected.
 * ========================================================================== */

import { motionOff, onMotionPreferenceChange, LATE_BOOT_MS } from './tokens.js';

const noop = () => {};

/* Cleanup from the previous initHero(). Kept module-scoped so a second call is
   idempotent rather than stacking a second pageshow listener. */
let teardown = null;

/* Missing in very old browsers and in non-DOM contexts. 0 means "booted early",
   which is the safe default: let the CSS cascade play. */
const bootTime = () =>
  typeof performance !== 'undefined' && performance.now ? performance.now() : 0;

/**
 * Guard the CSS hero cascade. Returns a cleanup function (never undefined, so
 * a caller can always invoke the result unconditionally).
 */
export function initHero() {
  if (teardown) teardown();

  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return (teardown = noop);
  }

  let hero = null;
  const settleHero = () => {
    if (hero) hero.classList.add('hero--settled');
  };

  try {
    // Interior pages use .page-hero, which carries no motion class at all — its
    // H1 is the LCP element on 20+ pages and must never gain a hidden state.
    // Only page-home.html:30 has `.hero`. Everywhere else this is a no-op.
    hero = document.querySelector('.hero, .banner');
    if (!hero) return (teardown = noop);

    // ?noanim, or reduced motion at boot. A media query cannot read a query
    // string, so this is the ONLY way ?noanim can neutralise a CSS keyframe.
    // Reduced motion is already handled by the reduce block in animations.css;
    // taking the same branch keeps one testable "everything visible, nothing
    // moves" path rather than two that can drift apart.
    if (motionOff()) {
      settleHero();
      return (teardown = noop);
    }

    // Late boot. The CSS cascade is finished at 770ms, so past LATE_BOOT_MS
    // (1200ms) this is a no-op in the normal case. It exists so that any future
    // change making the hero JS-triggered cannot replay an entrance on content
    // the visitor is already halfway through reading.
    if (bootTime() > LATE_BOOT_MS) {
      settleHero();
      return (teardown = noop);
    }

    // Mid-session flip to `reduce`: stop the cascade where it stands. Nothing
    // is animated back — motion simply stops and the final state lands.
    const unsub = onMotionPreferenceChange((reduced) => {
      if (reduced) settleHero();
    });

    // Back/forward cache restore. The visitor is returning to content they have
    // already read; an entrance replay there is disorienting, not welcoming.
    const onPageShow = (e) => {
      if (e.persisted) settleHero();
    };
    window.addEventListener('pageshow', onPageShow);

    const cleanup = () => {
      unsub();
      window.removeEventListener('pageshow', onPageShow);
      // only clear if a later init has not already replaced us
      if (teardown === cleanup) teardown = null;
    };

    teardown = cleanup;
    return cleanup;
  } catch (err) {
    // A guard must never leave the hero worse off than no JS at all.
    settleHero();
    return (teardown = noop);
  }
}
