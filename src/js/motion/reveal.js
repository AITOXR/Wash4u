/* ============================================================================
 * src/js/motion/reveal.js
 *
 * Scroll reveal. One gesture — fade + rise — at two amplitudes: 24px for a
 * block, 16px for a list child. That amplitude split is the whole design: a
 * section head travelling further than the grid beneath it hands the eye a
 * reading order for free, and stops forty fade-ups reading as a template.
 *
 * The contract with animations.css is that the hidden state is OPACITY ONLY.
 * Travel lives here, in the Motion keyframes, and nowhere else — so a bundle
 * that 404s can fade content in late but can never strand it at an offset.
 *
 * Nothing above the fold is touched. `.hero` is CSS-owned (the bundle is
 * `defer`; a keyframe starts at first paint and a deferred bundle does not).
 * ========================================================================== */

import { animate } from 'motion/mini';
import { inView } from 'motion';

import {
  BLOCK_DELAY,
  DUR,
  EASE,
  MOTION_OFF,
  NEVER_ANIMATE,
  REVEALED,
  VIEW,
  Y,
  cappedStagger,
  fadeUp,
  motionOff,
  onMotionPreferenceChange,
} from './tokens.js';

/** Every motion hook in the markup. Kept in one place so JS and CSS agree. */
const HOOKS = '.reveal, .stagger-children';

/** The four ladder classes already present in the templates. */
const DELAY_CLASSES = Object.keys(BLOCK_DELAY);

/** Per-item stagger, index clamped so a 12-card grid tails at 0.30s, not 0.66s. */
const stepFor = cappedStagger();

/* ---------------------------------------------------------------------------
 * SHARED HELPERS
 * ------------------------------------------------------------------------- */

/** Drop the inline values motion/mini commits on finish. Order-free. */
function release(el) {
  el.style.opacity = '';
  el.style.transform = '';
}

/**
 * Commit-then-release. The class must land BEFORE the inline styles go, or
 * `.js .reveal { opacity: 0 }` re-hides the element for a frame.
 *
 * The release matters because motion/mini writes the final value as an inline
 * style in NativeAnimation.onfinish and then cancels — so without this every
 * revealed element keeps `transform: none` forever and permanently outranks any
 * future CSS `:hover { transform: ... }`. Costs nothing; keeps "CSS owns hover"
 * enforceable.
 */
function finish(el) {
  el.classList.add(REVEALED);
  release(el);
}

/** Same, for a stagger container: the class is on the parent, the styles on the kids. */
function finishList(container, kids) {
  container.classList.add(REVEALED);
  for (let i = 0; i < kids.length; i++) release(kids[i]);
}

/**
 * Force a hook to its final visible state with no animation at all.
 * Used by the never-animate list, the focus guard and every off switch.
 */
function settle(el) {
  if (!el || !el.classList) return;
  el.classList.add(REVEALED);
  release(el);
  if (el.classList.contains('stagger-children')) {
    const kids = el.children;
    for (let i = 0; i < kids.length; i++) release(kids[i]);
  }
}

/**
 * The one guarantee this module owes the page: nothing stays hidden.
 * Safe to call at any time, from anywhere, including as an `error` handler
 * (the event argument is ignored) and before initReveal has ever run.
 */
export function settleAll() {
  if (typeof document === 'undefined') return;
  document.documentElement.classList.add(MOTION_OFF);
  document.querySelectorAll(HOOKS).forEach(settle);
}

/** The `reveal-delay-N` class this element carries, or null. */
function delayClassOf(el) {
  for (let i = 0; i < DELAY_CLASSES.length; i++) {
    if (el.classList.contains(DELAY_CLASSES[i])) return DELAY_CLASSES[i];
  }
  return null;
}

/* ---------------------------------------------------------------------------
 * INIT
 * ------------------------------------------------------------------------- */

/** Module-level so a second initReveal() is a no-op rather than a double bind. */
let teardown = null;

export function initReveal() {
  // EFFECT 1 — the net goes up before anything that could throw into it.
  // This is the only cover for a mid-boot exception, so it must be statement one.
  window.addEventListener('error', settleAll, { once: true });

  if (teardown) return teardown;

  const noop = () => {};

  try {
    // Off switch: ?noanim, reduced motion at boot, or no IntersectionObserver.
    // Settle rather than merely skipping animate() — the hidden state is a CSS
    // rule, so skipping the animation would leave every block blank.
    // Disarm the CSS failsafe. animations.css arms every hidden hook with
    // `motion-failsafe ... 1400ms forwards` so a bundle that never boots cannot
    // leave content invisible. Now that we HAVE booted, that keyframe must be
    // cancelled: otherwise it fires at 1400ms and forces opacity:1 on hooks
    // that have not been scrolled to yet, and Motion then re-hides each one as
    // it animates — a visible flash on every below-the-fold reveal.
    document.documentElement.classList.add('motion-ready');

    if (motionOff()) {
      settleAll();
      return noop;
    }

    // EFFECT 2 — partition, in this order: never-animate, hero-owned, observed.
    const all = Array.from(document.querySelectorAll(HOOKS));
    const observed = [];

    for (let i = 0; i < all.length; i++) {
      const el = all[i];

      // (a) Legal bodies, the live contact form, the 404 escape route, SEO price
      // rows and the preloaded LCP image. These must never reach opacity 0.
      if (NEVER_ANIMATE.some((sel) => el.matches(sel) || el.closest(sel))) {
        settle(el);
        continue;
      }

      // (b) Above the fold. animations.css owns the hero cascade and hero.js
      // guards it — touching these from a deferred bundle is what we are fixing.
      // `.page-hero` is the interior-page equivalent of `.hero` and is equally
      // above the fold on ~100 pages. Without it, their first block sits at
      // opacity 0 waiting on a deferred bundle.
      if (el.closest('.hero, .page-hero, .banner')) {
        settle(el);
        continue;
      }

      // A hook contained by another hook would animate the same subtree twice
      // (real on every service-detail page: a .stagger-children list inside a
      // .reveal block). Settle it rather than skipping — a bare `continue`
      // leaves its children at the CSS opacity:0 with nothing left to reveal
      // them, which blanks the list permanently.
      if (el.parentElement && el.parentElement.closest(HOOKS)) {
        settle(el);
        continue;
      }

      observed.push(el);
    }

    const stops = [];   // inView unsubscribers
    const live = [];    // running controls, so cleanup can stop them

    /**
     * EFFECT 5 — stagger reveal. Children travel 16px against their anchor's
     * 24px: six cards each moving 24px is six times the perceived motion of one
     * block moving 24px, and the split is what keeps a grid reading as one unit.
     */
    const runList = (list, baseDelay) => {
      const kids = Array.from(list.children);
      // animate() throws on an empty element list, and an empty container has
      // nothing to reveal anyway.
      if (!kids.length) {
        settle(list);
        return;
      }
      const c = animate(kids, fadeUp(Y.child), {
        duration: DUR.child,
        ease: EASE.enter,
        delay: (i) => baseDelay + stepFor(i),
      });
      // .then() resolves exactly once for the whole batch; onComplete would fire
      // once per element-per-property, i.e. 2N times for a list.
      c.then(() => finishList(list, kids));
      live.push(c);
    };

    // EFFECT 3 — pairing. A split section is two hooks with one timeline, fired
    // from ONE observer on the first member, so the partner column can no longer
    // land on the wrong element when the media column reorders above the copy.
    for (let i = 0; i < observed.length; i++) {
      const anchor = observed[i];
      const members = [{ el: anchor, delay: 0 }];

      const next = observed[i + 1];
      if (next) {
        const dc = delayClassOf(next);
        // Same section, and the partner actually asks for a delay. A lone
        // delayed hook (page-contact, whose anchor is in the never-animate set)
        // stays at 0 — it must not wait on a partner that will never animate.
        if (dc && anchor.closest('section') === next.closest('section')) {
          members.push({ el: next, delay: BLOCK_DELAY[dc] || 0 });
          i++;
        }
      }

      // EFFECT 4 — block reveal. 24px, 550ms, ease-out, triggered when the top
      // crosses ~88% of the viewport (VIEW's -12% margin).
      let stop = null;
      let fired = false;

      stop = inView(
        anchor,
        () => {
          if (fired) return;
          fired = true;
          if (stop) stop(); // belt and braces on top of inView's auto-unobserve

          try {
            for (let m = 0; m < members.length; m++) {
              const { el, delay } = members[m];
              if (el.classList.contains('stagger-children')) {
                runList(el, delay);
                continue;
              }
              const c = animate(el, fadeUp(Y.block), {
                duration: DUR.block,
                ease: EASE.enter,
                delay,
              });
              c.then(() => finish(el));
              live.push(c);
            }
          } catch (_) {
            // A group that cannot animate must still end up readable.
            for (let m = 0; m < members.length; m++) settle(members[m].el);
          }
        },
        VIEW
      );

      if (stop) stops.push(stop);
    }

    // EFFECT 6 — focus guard. opacity:0 removes nothing from the tab order, so
    // an un-revealed `.areas` (10 links) or `.blog-grid` (12) is briefly a set of
    // invisible focusable controls. Tabbing scrolls the element in and fires the
    // observer anyway, so the real window is about a frame — this closes it.
    const onFocusIn = (e) => {
      const t = e.target;
      const hook = t && t.closest ? t.closest(HOOKS) : null;
      if (hook && !hook.classList.contains(REVEALED)) settle(hook);
    };
    document.addEventListener('focusin', onFocusIn);

    // EFFECT 7 — a mid-session flip to `reduce` has to be answered here: the CSS
    // @media block cannot reach an inline style written by WAAPI. Nothing is
    // animated back; motion simply stops.
    const unsub = onMotionPreferenceChange((reduced) => {
      if (reduced) settleAll();
    });

    teardown = () => {
      if (!teardown) return;
      teardown = null;
      for (let i = 0; i < stops.length; i++) {
        try { stops[i](); } catch (_) {}
      }
      for (let i = 0; i < live.length; i++) {
        try { live[i].stop(); } catch (_) {}
      }
      document.removeEventListener('focusin', onFocusIn);
      window.removeEventListener('error', settleAll);
      unsub();
      // Last, so it clears the inline styles .stop() just committed.
      settleAll();
    };

    return teardown;
  } catch (_) {
    settleAll();
    return noop;
  }
}
