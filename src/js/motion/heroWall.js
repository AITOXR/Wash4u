/* ============================================================================
 * src/js/motion/heroWall.js
 *
 * Release the hero wall's compositor layers when the hero is off screen.
 *
 * The wall runs ten infinite transform animations, each on a `will-change:
 * transform` column. Measured: at the bottom of the page — with the hero
 * 13,000px above the viewport — all ten still reported playState "running"
 * and will-change still computed to "transform", so ten promoted layers stood
 * for the whole session for decoration nobody could see, and the sticky
 * header's backdrop-filter had to recomposite over them on every scroll.
 *
 * IntersectionObserver only. No scroll listener, so iOS momentum scrolling is
 * untouched. Zero visual change: on screen, the wall behaves exactly as it did.
 *
 * The CSS pause rule is gated on `html.wall-gated`, which only this module
 * adds — so a blocked or 404'd bundle leaves the wall running rather than
 * freezing it at first paint.
 * ========================================================================== */

import { inView } from 'motion';

export function initHeroWall() {
  const hero = document.querySelector('.home-hero');
  if (!hero || typeof IntersectionObserver === 'undefined') return () => {};

  // Set before arming the gate: the hero is on screen at boot, and arming
  // first would pause the wall for one frame.
  hero.classList.add('is-onscreen');
  document.documentElement.classList.add('wall-gated');

  // `amount: 'some'`, not the -12% reveal margin — this is a visibility gate,
  // not a reveal trigger, and it must release only once the hero is fully past.
  const stop = inView(hero, (el) => {
    el.classList.add('is-onscreen');
    return () => el.classList.remove('is-onscreen');
  }, { amount: 'some' });

  return () => {
    stop();
    hero.classList.remove('is-onscreen');
    document.documentElement.classList.remove('wall-gated');
  };
}
