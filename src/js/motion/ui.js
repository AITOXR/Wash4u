/* UI behaviour: mobile nav, FAQ disclosure, review-rail arrows, touch press.

   Nothing in this file animates, and nothing in it imports Motion. Every
   visible transition here already belongs to CSS — the nav panel
   (layout.css:105-123), the FAQ disclosure and its chevron (ui.css), the
   :active press states — so a full-screen fixed overlay's resting position
   and a button's press feedback never depend on the bundle arriving.

   What JS adds is only the part CSS cannot express: focus management, aria
   state, a focus trap, and a scroll step measured from the real card pitch.

   Replaces main.js:45-133. Three shipped defects die here:
     - openMenu/closeMenu dereferenced menuToggle with no internal guard
     - the FAQ wrote style.height against a property with no transition
     - the rail arrows were scoped to .testimonial-rail-wrap, a SIBLING of
       the .reviews-head they actually live in, so they did nothing
   The service-tab block (main.js:81-93) is deleted, not ported: .svc-tabs
   appears in no template in the tree.
*/

import { motionOff } from './tokens.js'

/* Stable reference so the touch-parity listener can be removed again. */
const noop = () => {}

/* Module-level so a second initUI() is a no-op rather than a double-bind. */
let teardown = null

export function initUI() {
  if (teardown) return teardown

  const cleanups = []

  const on = (target, type, fn, opts) => {
    if (!target) return
    target.addEventListener(type, fn, opts)
    cleanups.push(() => target.removeEventListener(type, fn, opts))
  }

  initMobileNav(on, cleanups)
  initNavDropdowns(on)
  initFaq(on)
  initRails(on, cleanups)

  // iOS Safari does not apply :active unless a touch handler is attached to
  // the element or one of its ancestors. One no-op listener on the document
  // is the entire touch-parity fix, and it leaves the press affordances in
  // CSS where a failed bundle cannot take them away.
  on(document, 'touchstart', noop, { passive: true })

  teardown = () => {
    cleanups.forEach((fn) => fn())
    cleanups.length = 0
    teardown = null
  }
  return teardown
}

/* ---------------------------------------------------------------------------
   EFFECT 1 — mobile nav

   CSS keeps the panel: opacity + transform + a `visibility 0s 220ms` delay
   that correctly removes it from the accessibility tree and the tab order
   when closed. Motion must not touch it; an inline transform would desync
   that visibility timing.
   ------------------------------------------------------------------------- */
function initMobileNav(on, cleanups) {
  const nav = document.getElementById('mobile-nav')
  if (!nav) return

  const toggle = document.getElementById('menu-toggle')
  const closeBtn = document.getElementById('menu-close')

  let lastFocus = null
  let prevOverflow = ''

  const isOpen = () => nav.classList.contains('is-open')

  const focusables = () =>
    Array.from(nav.querySelectorAll('a[href], button:not([disabled])'))

  const open = () => {
    if (isOpen()) return
    lastFocus = document.activeElement
    // record what the page already had rather than assuming '', so a scroll
    // lock set by anything else survives this panel closing
    prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    nav.classList.add('is-open')
    nav.setAttribute('aria-hidden', 'false')
    if (toggle) toggle.setAttribute('aria-expanded', 'true')
    // the first nav link, not the logo the shipped code landed on
    const first = nav.querySelector('.mobile-nav__link') || focusables()[0]
    if (first) first.focus()
  }

  const close = () => {
    if (!isOpen()) return
    // focus must leave BEFORE aria-hidden lands, or the focused element ends
    // up sitting inside an aria-hidden subtree
    const back = lastFocus instanceof HTMLElement ? lastFocus : toggle
    if (back && typeof back.focus === 'function') back.focus()
    // .menu-toggle is display:none above 62rem, so that focus() can silently
    // fail after a resize — never leave focus inside the panel we are hiding
    const active = document.activeElement
    if (active && nav.contains(active) && typeof active.blur === 'function') active.blur()

    if (toggle) toggle.setAttribute('aria-expanded', 'false')
    nav.setAttribute('aria-hidden', 'true')
    nav.classList.remove('is-open')
    document.body.style.overflow = prevOverflow
    lastFocus = null
  }

  // Escape stays on the document, as it was before: tapping the panel's own
  // background drops focus to <body>, and a panel-scoped handler would never
  // see the keypress. Tab is trapped from here for the same reason — the
  // page behind the fixed panel is still fully tabbable.
  const onKeydown = (e) => {
    if (!isOpen()) return
    if (e.key === 'Escape') {
      close()
      return
    }
    if (e.key !== 'Tab') return

    const items = focusables()
    if (!items.length) return
    const first = items[0]
    const last = items[items.length - 1]
    const active = document.activeElement
    const outside = !active || !nav.contains(active)

    if (e.shiftKey) {
      if (outside || active === first) {
        e.preventDefault()
        last.focus()
      }
    } else if (outside || active === last) {
      e.preventDefault()
      first.focus()
    }
  }

  on(toggle, 'click', open)
  on(closeBtn, 'click', close)
  on(document, 'keydown', onKeydown)
  // every link closes the panel; navigation follows normally
  nav.querySelectorAll('a[href]').forEach((a) => on(a, 'click', close))

  // teardown must not leave the page scroll-locked behind an open panel
  cleanups.push(() => {
    if (isOpen()) close()
  })
}

/* ---------------------------------------------------------------------------
   Header dropdowns (Services / Pricing mega-menus)

   The panel is shown by CSS on :hover and :focus-within, so it works for
   mouse and keyboard with no JS at all. This only keeps aria-expanded in
   sync with that state and closes the panel on Escape — progressive, never
   load-bearing.
   ------------------------------------------------------------------------- */
function initNavDropdowns(on) {
  const groups = Array.from(document.querySelectorAll('[data-dropdown]'))
  if (!groups.length) return

  const setOpen = (group, open) => {
    const trigger = group.querySelector('.header__link--parent')
    if (trigger) trigger.setAttribute('aria-expanded', open ? 'true' : 'false')
  }

  groups.forEach((group) => {
    on(group, 'mouseenter', () => setOpen(group, true))
    on(group, 'mouseleave', () => setOpen(group, false))
    on(group, 'focusin', () => setOpen(group, true))
    on(group, 'focusout', (e) => {
      if (!group.contains(e.relatedTarget)) setOpen(group, false)
    })
  })

  on(document, 'keydown', (e) => {
    if (e.key !== 'Escape') return
    const active = document.activeElement
    groups.forEach((g) => setOpen(g, false))
    // drop focus out of the panel so :focus-within releases it too
    if (active && active.closest && active.closest('[data-dropdown]') && active.blur) {
      active.blur()
    }
  })
}

/* ---------------------------------------------------------------------------
   EFFECT 2 — FAQ accordion

   State only. The open/close is `grid-template-rows: 0fr -> 1fr` in CSS, so
   there is no measurement, no ResizeObserver and no race with font loading.
   Every style.height write from main.js:107/114 is gone.
   ------------------------------------------------------------------------- */
function initFaq(on) {
  const items = Array.from(document.querySelectorAll('.faq-item'))
  if (!items.length) return

  const closeAll = () => {
    items.forEach((other) => {
      other.classList.remove('is-open')
      const q = other.querySelector('.faq-item__question')
      if (q) q.setAttribute('aria-expanded', 'false')
    })
  }

  items.forEach((item) => {
    const q = item.querySelector('.faq-item__question')
    if (!q) return
    const answer = item.querySelector('.faq-item__answer')

    // The macro emits aria-controls on the button and a matching id +
    // role="region" on the answer, but the region has no accessible name.
    // Naming it from its own question needs no template edit.
    if (answer) {
      if (!q.id && answer.id) q.id = answer.id + '-q'
      if (q.id && !answer.hasAttribute('aria-labelledby')) {
        answer.setAttribute('aria-labelledby', q.id)
      }
    }

    on(q, 'click', () => {
      const wasOpen = item.classList.contains('is-open')
      closeAll()
      if (wasOpen) return // a second click on an open item closes it
      item.classList.add('is-open')
      q.setAttribute('aria-expanded', 'true')
    })
  })
}

/* ---------------------------------------------------------------------------
   EFFECT 3 — review rail arrows

   Native scrolling only. .review-rail has `scroll-snap-type: x mandatory`
   and hardware momentum on touch; driving scrollLeft from rAF would fight
   the snap and downgrade the gesture that actually gets used.
   ------------------------------------------------------------------------- */
function initRails(on, cleanups) {
  const buttons = Array.from(document.querySelectorAll('[data-rail-prev], [data-rail-next]'))
  if (!buttons.length) return

  const rails = new Map()

  buttons.forEach((btn) => {
    // the buttons sit in .reviews-head, a sibling of the rail's wrapper, so
    // scope up to the section — this is the bug that made the arrows inert
    const section = btn.closest('section')
    const rail = section && section.querySelector('.review-rail')
    if (!rail) return

    let group = rails.get(rail)
    if (!group) {
      group = { prev: [], next: [] }
      rails.set(rail, group)
    }
    const isNext = btn.hasAttribute('data-rail-next')
    ;(isNext ? group.next : group.prev).push(btn)

    on(btn, 'click', () => {
      const kids = rail.children
      // one real card pitch, measured — immune to the gap token changing,
      // unlike the shipped `width + 24` which hardcoded var(--s-4)
      const step = kids.length > 1
        ? kids[1].offsetLeft - kids[0].offsetLeft
        : rail.clientWidth * 0.9
      rail.scrollBy({
        left: (isNext ? 1 : -1) * step,
        // `scroll-behavior: auto !important` in the reduce block cannot reach
        // an explicit behavior argument, so branch it here instead
        behavior: motionOff() ? 'auto' : 'smooth'
      })
    })
  })

  rails.forEach((group, rail) => {
    let ticking = false

    const sync = () => {
      ticking = false
      const max = rail.scrollWidth - rail.clientWidth
      const atStart = rail.scrollLeft <= 1
      const atEnd = rail.scrollLeft >= max - 1
      group.prev.forEach((b) => { b.disabled = atStart })
      group.next.forEach((b) => { b.disabled = atEnd })

      // disabling the button under the keyboard would drop focus to <body>;
      // hand it to the opposite arrow instead
      const active = document.activeElement
      if (active && active.disabled) {
        if (group.next.indexOf(active) > -1 && group.prev[0] && !group.prev[0].disabled) {
          group.prev[0].focus()
        } else if (group.prev.indexOf(active) > -1 && group.next[0] && !group.next[0].disabled) {
          group.next[0].focus()
        }
      }
    }

    // rAF-throttled: scrollLeft/scrollWidth are read at most once per frame,
    // and never from inside the click path
    const request = () => {
      if (ticking) return
      ticking = true
      requestAnimationFrame(sync)
    }

    on(rail, 'scroll', request, { passive: true })
    on(window, 'resize', request, { passive: true })
    sync()

    // leave nothing disabled behind us
    cleanups.push(() => {
      group.prev.concat(group.next).forEach((b) => { b.disabled = false })
    })
  })
}
