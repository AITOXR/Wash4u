import { motion } from 'framer-motion'
import { site } from '../content'
import Button from '../components/ui/Button'
import Stars from '../components/ui/Stars'

const fade = (delay) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.55, delay, ease: 'easeOut' },
})

export default function Hero() {
  return (
    <section id="top" className="overflow-hidden bg-white">
      <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 pb-14 pt-10 md:px-8 md:pb-20 md:pt-16 lg:grid-cols-[1.05fr_1fr] lg:gap-16">
        <div>
          <motion.h1
            {...fade(0)}
            className="font-display text-[3.4rem] leading-[0.98] uppercase text-teal md:text-[5rem]"
          >
            Gurugram's laundry,
            <br />
            picked up, cleaned,
            <br />
            delivered.
          </motion.h1>

          <motion.p {...fade(0.1)} className="mt-5 max-w-md text-lg leading-relaxed text-ink2">
            Free doorstep pickup & delivery, back in 24 hours — cleaned with
            eco-friendly Italian hydrocarbon technology.
          </motion.p>

          <motion.div {...fade(0.2)} className="mt-8 flex flex-wrap items-center gap-4">
            <Button href={site.booking} external size="lg">
              Schedule a Pickup
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>
            </Button>
            <Button href="#pricing" variant="secondary" size="lg">
              See Pricing
            </Button>
          </motion.div>

          <motion.div {...fade(0.3)} className="mt-7 flex items-center gap-2.5">
            <Stars />
            <span className="text-[0.95rem] font-medium text-ink2">
              {site.rating} rating · {site.reviews} happy customers
            </span>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.15, ease: 'easeOut' }}
          className="relative"
        >
          <div
            aria-hidden="true"
            className="absolute -right-16 -top-12 -z-10 h-72 w-72 rounded-full bg-mist blur-2xl"
          />
          <img
            src="./images/hero-banner.jpg"
            alt="Freshly cleaned, neatly folded laundry"
            width="1600"
            height="1333"
            fetchPriority="high"
            className="aspect-[6/5] w-full rounded-[28px] object-cover object-left shadow-[0_24px_48px_-12px_rgba(29,96,118,0.25)] ring-1 ring-black/5"
          />
          <div className="absolute -left-3 bottom-7 flex items-center gap-2.5 rounded-full bg-white py-2.5 pl-3 pr-5 shadow-[0_8px_24px_rgba(30,31,33,0.14)] max-lg:left-3 max-lg:bottom-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" /></svg>
            </span>
            <span className="leading-tight">
              <span className="block text-sm font-bold text-ink">Eco-friendly cleaning</span>
              <span className="block text-xs text-ink3">Italian hydrocarbon technology</span>
            </span>
          </div>
        </motion.div>
      </div>

      {/* Trust strip */}
      <div className="border-y border-hairline">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-10 gap-y-2 px-5 py-5 md:px-8">
          {['Free pickup & delivery', '24-hour turnaround', 'Eco-friendly cleansers', 'Satisfaction guaranteed'].map(
            (item) => (
              <span key={item} className="flex items-center gap-2 text-sm font-medium text-ink3">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-turquoise"><polyline points="20 6 9 17 4 12" /></svg>
                {item}
              </span>
            ),
          )}
        </div>
      </div>
    </section>
  )
}
