import { useEffect, useState } from 'react'
import { site, nav } from '../content'
import Button from '../components/ui/Button'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState('')

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Scrollspy — highlight the nav link for the section in view
  useEffect(() => {
    const sections = nav
      .map((l) => document.getElementById(l.href.slice(1)))
      .filter(Boolean)
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(`#${e.target.id}`)
        })
      },
      { rootMargin: '-30% 0px -60% 0px' },
    )
    sections.forEach((s) => observer.observe(s))
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => (document.body.style.overflow = '')
  }, [open])

  return (
    <>
      <header
        className={`sticky top-0 z-50 bg-white/80 backdrop-blur-xl transition-shadow ${
          scrolled ? 'shadow-[0_1px_0_#e5e5e5,0_2px_12px_rgba(30,31,33,0.05)]' : ''
        }`}
      >
        <div className="mx-auto flex h-[76px] max-w-6xl items-center justify-between gap-6 px-5 md:px-8">
          <a href="#top" aria-label="Wash4You home" className="shrink-0">
            <img src="./images/logo-header.png" alt="Wash4You" width="781" height="144" className="h-9 w-auto" />
          </a>

          <nav className="hidden items-center gap-7 lg:flex" aria-label="Main">
            {nav.map((l) => (
              <a
                key={l.href}
                href={l.href}
                aria-current={active === l.href ? 'true' : undefined}
                className={`relative py-1 text-[0.95rem] font-medium transition-colors after:absolute after:inset-x-0 after:-bottom-0.5 after:h-0.5 after:origin-left after:scale-x-0 after:rounded-full after:bg-turquoise after:transition-transform after:duration-200 hover:text-turquoise ${
                  active === l.href ? 'text-teal after:scale-x-100' : 'text-ink'
                }`}
              >
                {l.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <a
              href={site.phoneHref}
              className="hidden items-center gap-1.5 text-sm font-semibold text-ink hover:text-turquoise xl:inline-flex"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-turquoise"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
              {site.phone}
            </a>
            <Button href={site.booking} external size="sm" className="hidden sm:inline-flex">
              Schedule Pickup
            </Button>
            <button
              className="rounded-lg p-1.5 text-ink lg:hidden"
              aria-label={open ? 'Close menu' : 'Open menu'}
              aria-expanded={open}
              onClick={() => setOpen(!open)}
            >
              {open ? (
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              ) : (
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile menu */}
      {open && (
        <div className="fixed inset-0 top-[76px] z-40 flex flex-col bg-white px-6 pb-8 lg:hidden">
          <nav className="flex flex-col" aria-label="Mobile">
            {nav.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="border-b border-hairline py-4 text-xl font-semibold text-ink"
              >
                {l.label}
              </a>
            ))}
          </nav>
          <div className="mt-auto flex flex-col gap-3 pt-8">
            <Button href={site.booking} external size="lg">
              Schedule Pickup
            </Button>
            <Button href={site.phoneHref} variant="secondary" size="lg">
              Call {site.phone}
            </Button>
          </div>
        </div>
      )}
    </>
  )
}
