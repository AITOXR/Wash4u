import { site, nav, areas, stores } from '../content'
import Icon from '../components/ui/Icon'

const socials = [
  {
    label: 'Facebook',
    href: site.social.facebook,
    icon: <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" fill="currentColor" stroke="none" />,
  },
  {
    label: 'Instagram',
    href: site.social.instagram,
    icon: (
      <>
        <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
        <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
        <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
      </>
    ),
  },
  {
    label: 'LinkedIn',
    href: site.social.linkedin,
    icon: (
      <g fill="currentColor" stroke="none">
        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
        <rect x="2" y="9" width="4" height="12" />
        <circle cx="4" cy="4" r="2" />
      </g>
    ),
  },
  {
    label: 'YouTube',
    href: site.social.youtube,
    icon: (
      <path
        fill="currentColor"
        stroke="none"
        d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"
      />
    ),
  },
]

export default function Footer() {
  return (
    <footer id="contact" className="bg-ink pb-8 pt-16 text-white/70">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <div className="grid gap-10 border-b border-white/10 pb-12 sm:grid-cols-2 lg:grid-cols-[1.5fr_0.8fr_1.3fr_1.1fr]">
          <div>
            <img src="./images/logo-white.png" alt="Wash4You" width="150" height="38" className="mb-5 h-9 w-auto" />
            <p className="max-w-xs text-[0.95rem] leading-relaxed">
              Premium laundry & dry cleaning with free doorstep pickup and delivery —
              powered by eco-friendly Italian hydrocarbon technology.
            </p>
            <div className="mt-5 flex gap-3">
              {socials.map((s) => (
                <a
                  key={s.label}
                  href={s.href}
                  target="_blank"
                  rel="noopener"
                  aria-label={s.label}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white/85 transition-colors hover:bg-turquoise hover:text-white"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">{s.icon}</svg>
                </a>
              ))}
            </div>
          </div>

          <div>
            <h3 className="mb-4 text-[0.8125rem] font-semibold uppercase tracking-[0.12em] text-white/50">
              Quick links
            </h3>
            {nav.map((l) => (
              <a key={l.href} href={l.href} className="block py-1.5 text-[0.95rem] hover:text-white">
                {l.label}
              </a>
            ))}
            <a href="#faq" className="block py-1.5 text-[0.95rem] hover:text-white">
              FAQ
            </a>
          </div>

          <div>
            <h3 className="mb-4 text-[0.8125rem] font-semibold uppercase tracking-[0.12em] text-white/50">
              Our stores
            </h3>
            {stores.map((s) => (
              <div key={s.name} className="mb-4">
                <p className="text-[0.95rem] font-semibold text-white/85">{s.name}</p>
                <p className="text-sm leading-relaxed text-white/55">{s.address}</p>
              </div>
            ))}
          </div>

          <div>
            <h3 className="mb-4 text-[0.8125rem] font-semibold uppercase tracking-[0.12em] text-white/50">
              Contact
            </h3>
            <a href={site.phoneHref} className="block py-1.5 text-[0.95rem] hover:text-white">
              {site.phone}
            </a>
            <a href={site.emailHref} className="block py-1.5 text-[0.95rem] hover:text-white">
              {site.email}
            </a>
            <a href={site.whatsapp} target="_blank" rel="noopener" className="block py-1.5 text-[0.95rem] hover:text-white">
              WhatsApp us
            </a>
            <p className="mt-3 text-sm text-white/45">
              Serving {areas.slice(0, 4).join(', ')} & more across Gurugram | NCR
            </p>
          </div>
        </div>

        <div
          className="font-display pointer-events-none select-none overflow-hidden whitespace-nowrap text-center uppercase leading-[0.85] text-white/5"
          style={{ fontSize: 'clamp(4rem, 13.5vw, 11rem)' }}
          aria-hidden="true"
        >
          Wash4You
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-6 text-sm text-white/45">
          <p>© {new Date().getFullYear()} Wash4You. All rights reserved.</p>
          <p>Legal business name — {site.legalName}</p>
        </div>
      </div>

      {/* Floating WhatsApp */}
      <a
        href={site.whatsapp}
        target="_blank"
        rel="noopener"
        aria-label="Chat on WhatsApp"
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-[#25d366] text-white shadow-[0_16px_40px_rgba(30,31,33,0.25)] transition-transform hover:scale-108"
      >
        <Icon name="whatsapp" size={26} />
      </a>
    </footer>
  )
}
