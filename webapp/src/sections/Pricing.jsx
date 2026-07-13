import { pricing, pricingNote, site } from '../content'
import SectionHeading from '../components/ui/SectionHeading'
import Reveal from '../components/ui/Reveal'
import Button from '../components/ui/Button'

export default function Pricing() {
  return (
    <section id="pricing" className="bg-cloud py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <Reveal>
          <SectionHeading
            center
            eyebrow="Pricing"
            title="Simple, transparent pricing"
            subtitle="Per-piece rates, no surprises. What you see is what you pay."
          />
        </Reveal>

        <div className="grid items-start gap-5 md:grid-cols-3">
          {pricing.map((cat, i) => (
            <Reveal key={cat.title} delay={i * 0.1}>
              <div
                className={`relative overflow-hidden rounded-[20px] bg-white shadow-[0_1px_2px_rgba(30,31,33,0.06)] ${
                  cat.popular ? 'ring-2 ring-turquoise' : 'ring-1 ring-hairline/70'
                }`}
              >
                {cat.popular && (
                  <span className="absolute right-4 top-4 rounded-full bg-turquoise px-3 py-1 text-xs font-bold uppercase tracking-wide text-white">
                    Most popular
                  </span>
                )}
                <div className="bg-ink px-7 py-5">
                  <h3 className="text-lg font-semibold text-white">{cat.title}</h3>
                </div>
                <ul className="px-7 py-4">
                  {cat.items.map((item) => (
                    <li key={item.name} className="flex items-baseline gap-2.5 py-2.5">
                      <span className="text-[0.95rem] text-ink2">{item.name}</span>
                      <span
                        aria-hidden="true"
                        className="flex-1 -translate-y-1 border-b border-dotted border-hairline"
                      />
                      <span className="tabular whitespace-nowrap font-bold text-ink">
                        {item.price}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.25} className="mt-8 text-center">
          <p className="mb-6 text-sm text-ink3">{pricingNote}</p>
          <Button href={site.booking} external size="lg">
            Schedule a Pickup
          </Button>
        </Reveal>
      </div>
    </section>
  )
}
