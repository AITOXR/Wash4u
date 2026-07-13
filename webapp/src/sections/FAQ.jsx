import { useState } from 'react'
import { faqs } from '../content'
import SectionHeading from '../components/ui/SectionHeading'
import Reveal from '../components/ui/Reveal'

function FaqItem({ faq, open, onToggle }) {
  return (
    <div className="border-b border-hairline">
      <button
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 py-5 text-left text-[1.0625rem] font-semibold text-ink transition-colors hover:text-teal"
      >
        {faq.q}
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`shrink-0 text-ink3 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      <div
        className={`grid transition-[grid-template-rows] duration-300 ease-out ${
          open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        }`}
      >
        <div className="overflow-hidden">
          <p className="pb-5 leading-relaxed text-ink2">{faq.a}</p>
        </div>
      </div>
    </div>
  )
}

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState(0)

  return (
    <section id="faq" className="bg-white py-16 md:py-24">
      <div className="mx-auto max-w-3xl px-5 md:px-8">
        <Reveal>
          <SectionHeading center eyebrow="Questions" title="Frequently asked questions" />
        </Reveal>
        <Reveal delay={0.1}>
          {faqs.map((faq, i) => (
            <FaqItem
              key={faq.q}
              faq={faq}
              open={openIndex === i}
              onToggle={() => setOpenIndex(openIndex === i ? -1 : i)}
            />
          ))}
        </Reveal>
      </div>
    </section>
  )
}
