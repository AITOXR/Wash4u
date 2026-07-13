import { useState } from 'react'
import { areas, site } from '../content'
import SectionHeading from '../components/ui/SectionHeading'
import Reveal from '../components/ui/Reveal'
import Button from '../components/ui/Button'
import Icon from '../components/ui/Icon'

// Gurugram pincodes start with 122. Area names are matched fuzzily.
function checkAvailability(raw) {
  const q = raw.trim().toLowerCase()
  if (!q) return { status: 'empty', message: 'Enter your area name or pincode to check.' }

  const isPincode = /^\d+$/.test(q)
  if (isPincode) {
    if (!/^\d{6}$/.test(q)) {
      return { status: 'invalid', message: 'A pincode has 6 digits — please check and try again.' }
    }
    if (q.startsWith('122')) {
      return {
        status: 'yes',
        message: "You're in Gurugram — we serve most of the city with free pickup & delivery.",
      }
    }
    return {
      status: 'maybe',
      message: "We're mainly in Gurugram right now. Message us on WhatsApp — we'll confirm for your pincode.",
    }
  }

  const match = areas.find(
    (a) => a.toLowerCase().includes(q) || q.includes(a.toLowerCase()),
  )
  if (match) {
    return {
      status: 'yes',
      message: `Yes! ${match} is in our service area — free pickup & delivery included.`,
    }
  }
  if (q.includes('gurugram') || q.includes('gurgaon')) {
    return {
      status: 'yes',
      message: 'We serve most of Gurugram with free pickup & delivery.',
    }
  }
  return {
    status: 'maybe',
    message: "Not on our list yet — but we're expanding. Message us on WhatsApp and we'll confirm.",
  }
}

export default function AreaChecker() {
  const [value, setValue] = useState('')
  const [result, setResult] = useState(null)

  const onSubmit = (e) => {
    e.preventDefault()
    setResult(checkAvailability(value))
  }

  return (
    <section id="service-area" className="bg-white py-16 md:py-24">
      <div className="mx-auto max-w-4xl px-5 md:px-8">
        <div className="rounded-[28px] bg-mist px-6 py-12 text-center md:px-14 md:py-16">
        <Reveal>
          <SectionHeading
            center
            eyebrow="Service area"
            title="Are we in your neighbourhood?"
            subtitle="Enter your area or pincode — takes two seconds."
            className="mb-8 md:mb-10"
          />
        </Reveal>

        <Reveal delay={0.1}>
          <form onSubmit={onSubmit} noValidate className="mx-auto flex max-w-xl gap-2 max-sm:flex-col">
            <label htmlFor="area-input" className="sr-only">
              Area name or pincode
            </label>
            <input
              id="area-input"
              type="text"
              inputMode="text"
              placeholder="e.g. Sushant Lok or 122009"
              value={value}
              onChange={(e) => {
                setValue(e.target.value)
                if (result) setResult(null)
              }}
              className="w-full flex-1 rounded-full border-[1.5px] border-transparent bg-white px-6 py-3.5 text-base text-ink shadow-[0_1px_2px_rgba(30,31,33,0.06)] outline-none transition-colors placeholder:text-ink3 focus:border-turquoise focus:ring-4 focus:ring-turquoise/15"
            />
            <Button type="submit" size="lg" className="shrink-0">
              Check availability
            </Button>
          </form>

          <div aria-live="polite" className="mt-5 min-h-14">
            {result && (
              <div
                className={`mx-auto inline-flex max-w-xl items-start gap-2.5 rounded-2xl px-5 py-3.5 text-left text-[0.95rem] font-medium ${
                  result.status === 'yes'
                    ? 'bg-emerald-50 text-emerald-800'
                    : result.status === 'maybe'
                      ? 'bg-amber-50 text-amber-800'
                      : 'bg-cloud text-ink2'
                }`}
              >
                <span className="mt-0.5 shrink-0">
                  {result.status === 'yes' ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  ) : (
                    <Icon name="pin" size={18} />
                  )}
                </span>
                <span>
                  {result.message}{' '}
                  {result.status !== 'yes' && (
                    <a href={site.whatsapp} target="_blank" rel="noopener" className="font-bold text-teal underline">
                      Chat on WhatsApp
                    </a>
                  )}
                </span>
              </div>
            )}
          </div>
        </Reveal>

        <Reveal delay={0.2}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-ink3">
            Currently serving
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {areas.map((a) => (
              <span
                key={a}
                className="rounded-full bg-white px-4 py-1.5 text-sm font-medium text-teal shadow-[0_1px_2px_rgba(30,31,33,0.06)]"
              >
                {a}
              </span>
            ))}
          </div>
        </Reveal>
        </div>
      </div>
    </section>
  )
}
