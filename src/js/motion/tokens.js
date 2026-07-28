/* ============================================================================
 * src/js/motion/tokens.js
 *
 * The complete motion vocabulary for wash4you.in.
 * If a number is not in this file, it does not belong in an animation.
 *
 * VERIFIED against motion@12.42.2 in this repo's node_modules. Two facts drive
 * every choice below, both read from source, not from documentation:
 *
 *   1. The bundle imports `animate` from 'motion/mini' and `inView` from
 *      'motion'. Measured with this repo's own esbuild config
 *      (--bundle --format=iife --minify --target=es2019, gzip -9):
 *          animate + inView from 'motion'        64,906 raw / 23,261 gzip
 *          animate from 'motion/mini' + inView    8,678 raw /  3,444 gzip
 *          this file + both of the above          9,364 raw /  3,793 gzip
 *      Same reveals, 20 KB of gzip saved, on an audience defined as mid-tier
 *      Android on Gurugram mobile networks. `motion/mini` is the only correct
 *      entry point for this site. Never import from 'motion' except `inView`.
 *
 *   2. `motion/mini`'s animate is pure WAAPI (framer-motion/dist/es/animation/
 *      animators/waapi/animate-elements.mjs). That means:
 *        - keyframe keys are REAL CSS PROPERTY NAMES. There is no independent
 *          `y` / `scale` / `rotate`. Write `transform: ['translateY(24px)','none']`.
 *        - `type: 'spring'` throws an invariant (NativeAnimation.mjs). There are
 *          no springs on this site, which is also the brand position.
 *        - `delay` accepts a function `(i, total) => seconds` natively, so
 *          `stagger()` never needs importing.
 *        - `onComplete` fires after the final value is committed inline, and the
 *          returned group controls expose `.then()` which resolves once, after
 *          every animation in the batch has finished, and never rejects.
 *        - `duration` / `delay` are in SECONDS.
 * ========================================================================== */

/* ---------------------------------------------------------------------------
 * EASING
 *
 * Pass easing as a STRING, never as an imported function.
 * motion-dom/dist/es/animation/waapi/easing/supported.mjs maps 'easeOut' to
 * the native keyword "ease-out", which is cubic-bezier(0, 0, 0.58, 1) — byte
 * identical to the curve the /wash4y React app uses, since both projects sit
 * on 12.42.2. Passing the imported `easeOut` FUNCTION instead would route
 * through generateLinearEasing() and emit a multi-hundred-character linear()
 * string per animation, for an identical result. Strings cost zero bytes.
 *
 * The CSS token --ease-out (base.css:76) is cubic-bezier(.22, 1, .36, 1), an
 * expo-out with a hard front load. It stays exactly as it is for CSS
 * micro-interactions at <= 300ms, where the two curves are indistinguishable.
 * NEVER run both curves at the same duration on the same page: anything in CSS
 * at >= 400ms must use --ease-enter (added to base.css by this spec), which is
 * the same cubic-bezier(0, 0, .58, 1) that 'easeOut' resolves to here.
 * ------------------------------------------------------------------------- */
export const EASE = {
  /** Entrances. Everything that arrives. */
  enter: 'easeOut',
  /** Exits only. Exits are faster than entrances and use the opposite curve. */
  exit: 'easeIn',
};

/* ---------------------------------------------------------------------------
 * DURATION (seconds)
 *
 * Reveals sit in the 300-600ms scroll band; nothing here exceeds 550ms.
 * Contact feedback (hover, press, chevron, header state) is owned by CSS at
 * 150-300ms and is deliberately absent from this file.
 * ------------------------------------------------------------------------- */
export const DUR = {
  /** Above-the-fold hero beat. Shorter than a scroll reveal: it is already in view. */
  hero: 0.5,
  /** Block-level scroll reveal. The house standard, matching webapp Reveal.jsx. */
  block: 0.55,
  /** Stagger child. Shorter than its anchor so a long list still settles < 0.8s. */
  child: 0.45,
};

/* ---------------------------------------------------------------------------
 * TRAVEL (px) — AMPLITUDE ENCODES RANK
 *
 * This is the one rule that stops 40 fade-ups reading as a template. A section
 * heading travels further than the list beneath it, so the eye is given a
 * reading order for free even when both are on screen at once. Above the fold
 * travels least, because that content is already in view and needs no
 * entrance, only a settle.
 *
 * All three values sit inside the 8-24px "reads as a fade, not a slide" band.
 * DECLARED DIVERGENCE from the React app, which uses y: 28 in Reveal.jsx: 28
 * is outside that band and this site's anchors are full-bleed `.section-head`
 * blocks, wider than the app's column, so equal travel reads as more movement.
 * ------------------------------------------------------------------------- */
export const Y = {
  /** Hero copy beats. */
  hero: 20,
  /** Any `.reveal` block: section heads, split-section partners, CTA bands. */
  block: 24,
  /** Any `.stagger-children` child: cards, steps, promises, area links. */
  child: 16,
};

/* ---------------------------------------------------------------------------
 * KEYFRAME BUILDER
 *
 * The single source of the site's only motion gesture. WAAPI-shaped: explicit
 * two-keyframe arrays, so animateElements() never has to read computed style
 * to fill in a missing `from`, and `transform` rather than a non-existent `y`.
 * ------------------------------------------------------------------------- */
export const fadeUp = (px) => ({
  opacity: [0, 1],
  transform: [`translateY(${px}px)`, 'none'],
});

/* ---------------------------------------------------------------------------
 * STAGGER
 *
 * 0.06s per item is the top of the 0.02-0.06 interval band. The index is
 * clamped at 5, so the tail is 0.30s no matter how long the list is.
 * This matters concretely on the live templates:
 *     .areas          10 children  -> 0.30s tail (would be 0.54s uncapped)
 *     .svc-grid        9 children  -> 0.30s tail
 *     .service-grid   12 children  -> 0.30s tail
 *     .blog-grid      12 children  -> 0.30s tail
 * It replaces the eight hardcoded nth-child rules in animations.css, whose
 * `nth-child(n+8) { transition-delay: 420ms }` made every card past the 7th
 * arrive as one clump.
 *
 * A flat clamp rather than a per-row modulo: column counts change at every
 * breakpoint (.svc-grid is 1/2/3 across ui.css:306-312), so any hardcoded
 * column map is wrong on the majority mobile case.
 *
 * Returned shape matches what animateElements() calls: delay(i, total).
 * ------------------------------------------------------------------------- */
export const STAGGER = { step: 0.06, capIndex: 5 };

export const cappedStagger = (step = STAGGER.step, cap = STAGGER.capIndex) =>
  (i) => Math.min(i, cap) * step;

/* ---------------------------------------------------------------------------
 * CASCADE
 *
 * HERO_BEAT is the gap between hero copy beats, consumed by the CSS contract
 * in animations.css (90ms). Four perceptible beats; the care note rides with
 * the H1 on beat 0 so the headline is never the second thing to land.
 *
 * BLOCK_DELAY maps the `reveal-delay-N` classes that already exist in the
 * templates onto a real ladder. Only `reveal-delay-2` is used outside the
 * hero (page-about.html:18 and :31, page-location.html:37,
 * page-service-detail.html:36, page-contact.html:37 — always the partner
 * column of a two-column split), so in practice this is a single 0.10s
 * handoff: anchor at t=0, its partner at t=0.10, both fired from ONE observer.
 * That determinism is the point — today they are two independent
 * IntersectionObserver hits papered over by a hardcoded 160ms transition-delay
 * (animations.css:18), which lands on the wrong element whenever the media
 * column is reordered above the copy at narrow widths.
 * ------------------------------------------------------------------------- */
export const HERO_BEAT = 0.09;

export const BLOCK_DELAY = {
  'reveal-delay-1': 0.05,
  'reveal-delay-2': 0.10,
  'reveal-delay-3': 0.15,
  'reveal-delay-4': 0.20,
};

/* ---------------------------------------------------------------------------
 * VIEWPORT TRIGGER — the shared inView preset
 *
 * amount:'some' resolves to IntersectionObserver threshold 0
 * (framer-motion/dist/es/render/dom/viewport/index.mjs). This replaces the
 * shipped `threshold: 0.08` (main.js:164), which is a ratio of the ELEMENT,
 * not the viewport: any wrapper taller than ~12.5x the viewport can never
 * reach 8% visibility and stays at opacity:0 permanently. That is a silent
 * content-disappears bug, not a motion bug.
 *
 * -12% fires when the element's top crosses ~88% of viewport height, inside
 * the 85-90% guidance, and is resolution-independent — unlike the shipped
 * -30px, which is far too shallow and reads as twitchy, and unlike the React
 * app's fixed -70px, which is 92% of a desktop viewport but 85% of a phone.
 *
 * `once` is not an option in this API: returning nothing from the inView
 * callback makes it unobserve that element (verified in the source above).
 * The onEnd callback, when returned, receives (entry) — NOT (element, entry).
 * ------------------------------------------------------------------------- */
export const VIEW = { amount: 'some', margin: '0px 0px -12% 0px' };

/* ---------------------------------------------------------------------------
 * NEVER ANIMATE
 *
 * Elements that carry a motion class in markup but must never reach opacity 0.
 * Enforced TWICE: as CSS in animations.css (because the bundle is `defer`, so
 * a JS-only filter still leaves a real window at first paint in which an
 * entire legal page is invisible) and as this list in JS.
 *
 * - .policy-section   page-policy.html:12  — the entire body of 5 legal pages
 * - .contact-form     page-contact.html:13 — a whole <form>; opacity:0 on a
 *                     form makes it unusable, not merely invisible
 * - .page-404         page-404.html:6      — the only two links off the page,
 *                     on a page short enough that an observer may never fire
 * - .pricing-grid     page-pricing.html:14, page-steam-iron.html:33 — SEO
 *                     price rows on pages that currently have no live CSS at all
 * - .banner__art      page-home.html:60    — the LCP element (with its inner
 *                     .banner__mascot). The template preloads it with
 *                     fetchpriority="high" (page-home.html:6); an element at
 *                     opacity 0 has not painted, so hiding it postpones LCP
 *                     until a deferred bundle boots. Never touch it.
 * ------------------------------------------------------------------------- */
export const NEVER_ANIMATE = [
  '.policy-section',
  '.contact-form',
  '.page-404',
  '.pricing-grid',
  '.banner__art',
  '.banner__mascot',
];

/* ---------------------------------------------------------------------------
 * CLASS + TIMING CONTRACT SHARED WITH animations.css
 *
 * REVEALED replaces the old `.is-visible`. Renamed deliberately: any stale
 * `.is-visible` rule or handler left anywhere in the tree must fail loudly
 * rather than half-work.
 *
 * MOTION_OFF is added to <html> when JS decides not to animate at all
 * (?noanim, reduced motion at boot, or no IntersectionObserver). CSS uses it
 * to force every hidden hook visible. It is only ever ADDITIVE visibility, so
 * adding it after first paint can never cause a flash.
 *
 * FAILSAFE_MS must equal the animation-delay on the `motion-failsafe`
 * keyframe in animations.css. If the bundle 404s, is blocked, or throws before
 * booting, that CSS animation forces every hidden hook to opacity 1 at this
 * timestamp. It uses animation-fill-mode: forwards (never `both`, which would
 * back-fill opacity:0 during the delay and beat the .is-revealed rule), and it
 * animates opacity ONLY and never transform, so it can never strand content at
 * an offset and can never beat a CSS hover rule.
 * ------------------------------------------------------------------------- */
export const REVEALED = 'is-revealed';
export const MOTION_OFF = 'motion-off';
export const FAILSAFE_MS = 1400;

/**
 * If the bundle boots later than this, the visitor is already reading. Play
 * nothing above the fold and settle it instead — a late entrance animation on
 * content someone is mid-sentence through is worse than no animation.
 */
export const LATE_BOOT_MS = 1200;

/* ---------------------------------------------------------------------------
 * OFF SWITCH
 *
 * Live, not a snapshot. The shipped code reads `.matches` once into a const at
 * main.js:155 and never re-reads it. That is harmless today because nothing in
 * JS animates and CSS !important wins either way; it becomes a real bug the
 * moment Motion writes inline styles, which the CSS reduced-motion block
 * cannot reach.
 *
 * `?noanim` is the QA escape hatch, ported from webapp Reveal.jsx:4. It takes
 * exactly the same code path as reduced motion so there is one, testable
 * "everything visible, nothing moves" branch.
 *
 * Environment only — matchMedia and location. No document access, per the
 * module contract.
 * ------------------------------------------------------------------------- */
const reduceMQ =
  typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : null;

const noanim =
  typeof window !== 'undefined' &&
  new URLSearchParams(window.location.search).has('noanim');

/** True when the visitor has asked the OS to reduce motion. Read live. */
export const prefersReduced = () => Boolean(reduceMQ && reduceMQ.matches);

/** True when no JS-driven motion may run at all. Every animate() site checks this. */
export const motionOff = () =>
  noanim ||
  prefersReduced() ||
  typeof window === 'undefined' ||
  !('IntersectionObserver' in window);

/**
 * Subscribe to live changes of the reduced-motion preference.
 * Returns an unsubscribe function. Safari < 14 only has addListener.
 */
export const onMotionPreferenceChange = (fn) => {
  if (!reduceMQ) return () => {};
  const handler = (e) => fn(e.matches);
  if (reduceMQ.addEventListener) {
    reduceMQ.addEventListener('change', handler);
    return () => reduceMQ.removeEventListener('change', handler);
  }
  reduceMQ.addListener(handler);
  return () => reduceMQ.removeListener(handler);
};
