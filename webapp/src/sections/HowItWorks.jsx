import { steps, site } from '../content'
import SectionHeading from '../components/ui/SectionHeading'
import Reveal from '../components/ui/Reveal'
import Button from '../components/ui/Button'

const icons = [
  // calendar/phone — schedule
  <svg key="1" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="3" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /><path d="m9 16 2 2 4-4" /></svg>,
  // washing machine — clean
  <svg key="2" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="3" /><circle cx="12" cy="13" r="5" /><path d="M7 13c1.5 1.2 3.5 1.2 5 0s3.5-1.2 5 0" /><line x1="8" y1="6" x2="8.01" y2="6" /></svg>,
  // truck — deliver
  <svg key="3" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M5 18H3c-.6 0-1-.4-1-1V7c0-.6.4-1 1-1h10c.6 0 1 .4 1 1v11" /><path d="M14 9h4l4 4v4c0 .6-.4 1-1 1h-2" /><circle cx="7" cy="18" r="2" /><circle cx="17" cy="18" r="2" /></svg>,
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-cloud py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <Reveal>
          <SectionHeading
            center
            eyebrow="Simple & seamless"
            title="How it works"
            subtitle="Three steps between you and a laundry-free week."
          />
        </Reveal>

        <div className="relative grid gap-5 md:grid-cols-3 md:gap-6">
          <div
            aria-hidden="true"
            className="absolute left-[8%] right-[8%] top-24 hidden border-t-2 border-dashed border-turquoise/25 md:block"
          />
          {steps.map((step, i) => (
            <Reveal key={step.title} delay={i * 0.12} className="relative">
              <div className="relative h-full rounded-[20px] bg-white p-8 shadow-[0_1px_2px_rgba(30,31,33,0.06)] ring-1 ring-hairline/70">
                <span className="font-display absolute right-6 top-5 text-[3.5rem] leading-none text-mist select-none" aria-hidden="true">
                  {i + 1}
                </span>
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-mist text-teal">
                  {icons[i]}
                </div>
                <h3 className="mb-2 text-lg font-semibold text-ink">
                  {i + 1}. {step.title}
                </h3>
                <p className="text-[0.95rem] leading-relaxed text-ink2">{step.text}</p>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.3} className="mt-10 text-center">
          <Button href={site.booking} external size="lg">
            Schedule your first pickup
          </Button>
          <p className="mt-3 text-sm text-ink3">Takes under a minute · No payment needed to book</p>
        </Reveal>
      </div>
    </section>
  )
}
