import { site } from '../content'
import Reveal from '../components/ui/Reveal'
import Button from '../components/ui/Button'
import Icon from '../components/ui/Icon'
import Stars from '../components/ui/Stars'

export default function BookingCTA() {
  return (
    <section className="bg-cloud pb-16 md:pb-24">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <Reveal>
          <div className="rounded-[28px] bg-teal px-6 py-14 text-center md:px-16 md:py-20">
            <Stars size={22} className="mb-5 justify-center" />
            <h2 className="font-display mx-auto max-w-2xl text-[2.4rem] leading-[1.04] uppercase text-white md:text-[3.25rem]">
              Ready for a laundry-free week?
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-lg text-white/85">
              Book your free pickup in under a minute — on the web or straight from WhatsApp.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              <Button href={site.booking} external size="lg">
                Schedule a Pickup
              </Button>
              <Button
                href={site.whatsapp}
                external
                size="lg"
                className="bg-[#25d366] text-white hover:bg-[#1fb857]"
              >
                <Icon name="whatsapp" size={20} />
                Book on WhatsApp
              </Button>
            </div>
            <p className="mt-6 text-sm text-white/70">
              Or call us: <a href={site.phoneHref} className="font-semibold text-white underline">{site.phone}</a>
            </p>
            <div className="mx-auto mt-8 flex max-w-xl flex-wrap items-center justify-center gap-x-8 gap-y-2 border-t border-white/15 pt-6">
              {['Free pickup & delivery', '24-hour turnaround', 'Nothing to pay when you book'].map((t) => (
                <span key={t} className="flex items-center gap-2 text-sm font-medium text-white/75">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  {t}
                </span>
              ))}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}
