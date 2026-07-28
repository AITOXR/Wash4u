/* ============================================================================
 * src/js/motion/scroll.js
 *
 * Two scroll-position affordances: the sticky header's scrolled state, and the
 * fixed mobile booking bar. Neither is decoration, so neither is suppressed
 * under reduced motion — a customer who has asked for less movement still gets
 * a legible header and a reachable Book pickup button.
 *
 * There is no `scroll()` call in this file and no `animate()` call either.
 * Both effects are class toggles handed to transitions that already exist in
 * layout.css. Motion's only job here is `inView`, standing in for the hero
 * measurement the shipped code did on every scroll event.
 * ========================================================================== */

import { inView } from 'motion'

/* One live instance per page. Re-entry hands back the existing cleanup rather
   than stacking a second scroll listener on the same header. */
let active = null

export function initScroll() {
  if (active) return active

  const teardown = []

  /* ------------------------------------------------------------------------
   * EFFECT 1 — sticky header state
   *
   * .header--scrolled (layout.css:20) fades in a border and a shadow over the
   * 220ms transition at layout.css:18. That transition stays; this only flips
   * the class.
   * ---------------------------------------------------------------------- */
  const header = document.getElementById('header')

  if (header) {
    let ticking = false
    let raf = 0
    let on = false

    const read = () => {
      ticking = false
      const y = window.scrollY
      // Hysteresis: on at 24px, off at 12px. A single boundary means a
      // trackpad resting exactly on it strobes the whole header style set.
      if (!on && y > 24) {
        on = true
        header.classList.add('header--scrolled')
      } else if (on && y < 12) {
        on = false
        header.classList.remove('header--scrolled')
      }
    }

    const onScroll = () => {
      if (ticking) return
      ticking = true
      raf = requestAnimationFrame(read)
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    // Mid-page reload or a deep link lands already scrolled — get it right now
    // rather than on the visitor's first nudge. scrollY forces no reflow.
    read()

    teardown.push(() => {
      window.removeEventListener('scroll', onScroll)
      if (raf) cancelAnimationFrame(raf)
    })
  }

  /* ------------------------------------------------------------------------
   * EFFECT 2 — mobile booking bar
   *
   * Visible once the hero is off screen. The slide itself is CSS
   * (layout.css:216-232, transform-only, with a real enter and exit), so a
   * fixed overlay's resting position never depends on the bundle booting.
   *
   * The shipped version re-measured hero.offsetHeight inside an unthrottled
   * scroll handler — a forced sync layout on every event, for a number that
   * cannot change while scrolling. inView does the same job for zero
   * per-frame main-thread work.
   * ---------------------------------------------------------------------- */
  const bar = document.getElementById('mobile-cta-bar')

  if (bar) {
    const body = document.body
    const show = () => {
      bar.classList.add('is-visible')
      if (body) body.classList.add('has-cta-bar')
    }
    const hide = () => {
      bar.classList.remove('is-visible')
      if (body) body.classList.remove('has-cta-bar')
    }

    const hero = document.querySelector('.banner, .hero, .page-hero, .service-detail__hero')

    if (!hero) {
      // page-404 has no hero of any kind — the bar is the only persistent CTA
      // there, so show it immediately.
      show()
    } else {
      // The one case inView structurally cannot cover: the hero is already
      // above the viewport at boot, so it never *enters* and onStart never
      // fires. One rect read, at init only, never during a scroll.
      if (hero.getBoundingClientRect().bottom <= 0) show()

      // Returning a function from onStart is what keeps inView observing —
      // return nothing and it unobserves after the first hit. onEnd receives
      // (entry), not (element, entry).
      const stopBar = inView(hero, () => {
        hide()
        return () => show()
      }, { amount: 'some' })

      teardown.push(stopBar)
    }
  }

  active = () => {
    active = null
    teardown.forEach(fn => { try { fn() } catch (e) {} })
  }

  return active
}
