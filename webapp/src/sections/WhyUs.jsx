import { whyUs } from '../content'
import SectionHeading from '../components/ui/SectionHeading'
import Reveal from '../components/ui/Reveal'
import Icon from '../components/ui/Icon'

export default function WhyUs() {
  return (
    <section className="bg-cloud py-16 md:py-24">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <Reveal>
          <SectionHeading eyebrow="Why Wash4You" title="Why you'll love us" />
        </Reveal>
        <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
          {whyUs.map((item, i) => (
            <Reveal key={item.title} delay={i * 0.08}>
              <div className="mb-5 flex h-13 w-13 items-center justify-center rounded-full bg-mist text-teal">
                <Icon name={item.icon} size={24} />
              </div>
              <h3 className="mb-1.5 font-semibold text-ink">{item.title}</h3>
              <p className="text-[0.95rem] leading-relaxed text-ink2">{item.text}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
