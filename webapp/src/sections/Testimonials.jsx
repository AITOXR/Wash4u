import { testimonials, site } from '../content'
import SectionHeading from '../components/ui/SectionHeading'
import Reveal from '../components/ui/Reveal'
import Stars from '../components/ui/Stars'

export default function Testimonials() {
  return (
    <section className="bg-white py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <Reveal>
          <SectionHeading
            center
            eyebrow="Happy customers"
            title="Hear from customers like you"
            subtitle={`${site.rating} average rating from ${site.reviews} customers across Gurugram.`}
          />
        </Reveal>
        <div className="grid gap-5 md:grid-cols-3">
          {testimonials.map((t, i) => (
            <Reveal key={t.author} delay={i * 0.1}>
              <figure className="relative flex h-full flex-col overflow-hidden rounded-[20px] bg-white p-8 shadow-[0_1px_2px_rgba(30,31,33,0.06)] ring-1 ring-hairline/60">
                <span
                  aria-hidden="true"
                  className="font-display pointer-events-none absolute -top-3 right-5 select-none text-[6rem] leading-none text-mist"
                >
                  ”
                </span>
                <Stars className="mb-4" />
                <blockquote className="mb-6 flex-1 text-[1.0625rem] leading-relaxed text-ink">
                  “{t.quote}”
                </blockquote>
                <figcaption>
                  <span className="block font-semibold text-ink">{t.author}</span>
                  <span className="text-sm text-ink3">{t.location}</span>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
