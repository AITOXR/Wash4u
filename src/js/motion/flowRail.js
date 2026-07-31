/* ============================================================================
 * src/js/motion/flowRail.js
 *
 * The "How it works" rail on mobile: marks the step card that is FULLY in
 * view, and drives the swipe-progress bar.
 *
 * Only the active card is green (redesign-home.css). "Fully in view" is
 * measured against the rail, not the viewport, so an IntersectionObserver
 * rooted on the scroll container is the right tool — it reports ratios the
 * browser already computes, with no scroll-handler geometry of our own.
 *
 * Why not CSS: `@container scroll-state(snapped: x)` would do this with no
 * JS at all, but it is Chrome-133+ only. A visitor on Safari or Firefox would
 * see every card blue, which is worse than shipping ~60 lines.
 *
 * Two guards worth keeping:
 *   - Nothing runs above the mobile breakpoint. The desktop grid is not a
 *     scroller, every card is fully visible, and marking one "active" there
 *     would fight the hover state.
 *   - Cards are never left with a stale .is-active when the layout flips to
 *     the grid — the class is cleared on teardown.
 * ========================================================================== */

const RAIL = '.flow';
const STEP = '.flow__step';

/* Matches the max-width in redesign-home.css. Kept as one constant so the
   two cannot drift apart silently. */
const MOBILE = '(max-width: 47.99rem)';

/* A card counts as "fully on screen" a hair below 1. Sub-pixel rail widths
   and fractional scroll offsets mean an exactly-flush card often reports
   0.995, and a threshold of 1 makes the green state flicker or never land. */
const FULL = 0.92;

let teardown = null;

export function initFlowRail() {
  if (teardown) teardown();

  if (typeof document === 'undefined' || typeof window === 'undefined') {
    return (teardown = () => {});
  }

  const rail = document.querySelector(RAIL);
  if (!rail) return (teardown = () => {});

  const steps = Array.from(rail.querySelectorAll(STEP));
  const bar = document.querySelector('.flow-progress');
  if (!steps.length) return (teardown = () => {});

  const mq = window.matchMedia(MOBILE);
  let observer = null;
  let scrollBound = false;

  /* Fill fraction = one card's share, plus however far we have scrolled. So a
     rail parked at the start still shows a stub rather than an empty track,
     and the bar reaches 1 exactly at the end. */
  const setProgress = () => {
    if (!bar) return;
    const max = rail.scrollWidth - rail.clientWidth;
    const visible = rail.clientWidth / rail.scrollWidth;
    const travelled = max > 0 ? rail.scrollLeft / max : 0;
    const fill = visible + (1 - visible) * travelled;
    bar.style.setProperty('--flow-progress', Math.min(1, Math.max(0.06, fill)).toFixed(4));
  };

  const clear = () => steps.forEach((s) => s.classList.remove('is-active'));

  const start = () => {
    if (observer) return;

    // Ratio per card, so the winner can be picked across the whole set rather
    // than from whichever entry fired last.
    const ratios = new Map(steps.map((s) => [s, 0]));

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => ratios.set(e.target, e.intersectionRatio));

        let best = null;
        let bestRatio = 0;
        ratios.forEach((ratio, el) => {
          if (ratio >= FULL && ratio > bestRatio) {
            best = el;
            bestRatio = ratio;
          }
        });

        // No card fully visible (mid-swipe): keep the last active one rather
        // than dropping every card to blue for a few frames.
        if (!best) return;
        steps.forEach((s) => s.classList.toggle('is-active', s === best));
      },
      { root: rail, threshold: [0, 0.5, FULL, 0.99, 1] }
    );

    steps.forEach((s) => observer.observe(s));

    if (!scrollBound) {
      rail.addEventListener('scroll', setProgress, { passive: true });
      scrollBound = true;
    }
    setProgress();
  };

  const stop = () => {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    // The desktop grid must not inherit a green card from the rail.
    clear();
  };

  const apply = () => (mq.matches ? start() : stop());

  apply();

  // Safari < 14 has no addEventListener on MediaQueryList.
  if (mq.addEventListener) mq.addEventListener('change', apply);
  else if (mq.addListener) mq.addListener(apply);

  window.addEventListener('resize', setProgress);

  const cleanup = () => {
    stop();
    rail.removeEventListener('scroll', setProgress);
    window.removeEventListener('resize', setProgress);
    if (mq.removeEventListener) mq.removeEventListener('change', apply);
    else if (mq.removeListener) mq.removeListener(apply);
    if (teardown === cleanup) teardown = null;
  };

  teardown = cleanup;
  return cleanup;
}
