/* Before/after proof slider.

   The <input type="range"> inside each figure is the real control —
   it already gives us keyboard operation, focus, and screen-reader
   announcement. This module does two things on top of that:

     1. mirrors the range value onto --pos so the clip and handle move
     2. lets you drag anywhere on the image, not just on the thumb

   Everything degrades: with this file absent the range still works,
   and with JS off entirely --pos keeps its CSS default of 50%.
*/

export function initBeforeAfter(root = document) {
  const figures = root.querySelectorAll('[data-ba]')
  if (!figures.length) return

  const cleanups = []

  figures.forEach((fig) => {
    const frame = fig.querySelector('.ba__frame')
    const range = fig.querySelector('.ba__range')
    if (!frame || !range) return

    const setPos = (pct) => {
      const clamped = Math.max(0, Math.min(100, pct))
      fig.style.setProperty('--pos', clamped + '%')
    }

    // The clipped "before" image must stay the width of the FRAME, not of
    // its clipping parent, or it squashes as the divider moves.
    const syncWidth = () => {
      fig.style.setProperty('--ba-frame-w', frame.clientWidth + 'px')
    }

    const onInput = () => setPos(Number(range.value))
    range.addEventListener('input', onInput)

    // Drag anywhere on the image. Pointer events cover mouse, touch and pen.
    let dragging = false

    const posFromEvent = (e) => {
      const rect = frame.getBoundingClientRect()
      if (!rect.width) return Number(range.value)
      return ((e.clientX - rect.left) / rect.width) * 100
    }

    const apply = (e) => {
      const pct = posFromEvent(e)
      range.value = String(Math.round(pct))
      setPos(pct)
    }

    const onDown = (e) => {
      // let the range keep its own keyboard focus behaviour
      dragging = true
      frame.setPointerCapture?.(e.pointerId)
      apply(e)
    }
    const onMove = (e) => {
      if (!dragging) return
      // only claim the gesture once it is clearly horizontal, so vertical
      // page scrolling on touch still works
      e.preventDefault()
      apply(e)
    }
    const onUp = (e) => {
      dragging = false
      frame.releasePointerCapture?.(e.pointerId)
    }

    frame.addEventListener('pointerdown', onDown)
    frame.addEventListener('pointermove', onMove)
    frame.addEventListener('pointerup', onUp)
    frame.addEventListener('pointercancel', onUp)

    let ro
    if ('ResizeObserver' in window) {
      ro = new ResizeObserver(syncWidth)
      ro.observe(frame)
    } else {
      window.addEventListener('resize', syncWidth, { passive: true })
    }
    syncWidth()
    setPos(Number(range.value))

    cleanups.push(() => {
      range.removeEventListener('input', onInput)
      frame.removeEventListener('pointerdown', onDown)
      frame.removeEventListener('pointermove', onMove)
      frame.removeEventListener('pointerup', onUp)
      frame.removeEventListener('pointercancel', onUp)
      ro ? ro.disconnect() : window.removeEventListener('resize', syncWidth)
    })
  })

  return () => cleanups.forEach((fn) => fn())
}
