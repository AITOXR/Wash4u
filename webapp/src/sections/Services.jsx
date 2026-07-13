import { services } from '../content'
import SectionHeading from '../components/ui/SectionHeading'
import Reveal from '../components/ui/Reveal'
import Icon from '../components/ui/Icon'

export default function Services() {
  return (
    <section id="services" className="bg-white py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <Reveal>
          <SectionHeading
            eyebrow="Services"
            title="Everything your wardrobe needs"
            subtitle="One pickup covers it all — from everyday laundry to delicate couture, shoes, and home textiles."
          />
        </Reveal>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {services.map((s, i) => (
            <Reveal key={s.name} delay={(i % 4) * 0.08}>
              <div className="group flex h-full flex-col rounded-[20px] bg-white p-7 shadow-[0_1px_2px_rgba(30,31,33,0.06)] ring-1 ring-hairline/70 transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_6px_20px_rgba(30,31,33,0.08)] hover:ring-turquoise/40">
                <div className="mb-5 flex h-13 w-13 items-center justify-center rounded-2xl bg-mist text-teal transition-colors group-hover:bg-teal group-hover:text-white">
                  <Icon name={s.icon} size={24} />
                </div>
                <h3 className="mb-1.5 font-semibold text-ink">{s.name}</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink2">{s.text}</p>
                <span className="mt-auto text-sm font-bold text-teal">
                  from <span className="text-base">{s.from}</span>
                </span>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
