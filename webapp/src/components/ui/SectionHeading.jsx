export default function SectionHeading({
  eyebrow,
  title,
  subtitle,
  center = false,
  className = '',
}) {
  return (
    <div className={`max-w-2xl mb-12 md:mb-16 ${center ? 'mx-auto text-center' : ''} ${className}`}>
      {eyebrow && (
        <span className="inline-block text-[0.8125rem] font-semibold uppercase tracking-[0.12em] text-turquoise mb-3">
          {eyebrow}
        </span>
      )}
      <h2 className="font-display text-[2.4rem] leading-[1.04] md:text-[3.25rem] uppercase text-teal">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-[1.0625rem] md:text-lg leading-relaxed text-ink2">{subtitle}</p>
      )}
    </div>
  )
}
