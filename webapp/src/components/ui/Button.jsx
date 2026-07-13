const styles = {
  primary:
    'bg-orange text-white hover:bg-orange-dark hover:-translate-y-px hover:shadow-lg hover:shadow-orange/20',
  secondary:
    'bg-white text-ink border-[1.5px] border-hairline hover:border-ink',
  ghost: 'text-teal hover:text-turquoise',
}

const sizes = {
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-3.5 text-[1.0625rem]',
  sm: 'px-4 py-2 text-sm',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  href,
  external = false,
  className = '',
  children,
  ...props
}) {
  const cls = `inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-all duration-150 focus-visible:outline-3 focus-visible:outline-turquoise focus-visible:outline-offset-2 ${styles[variant]} ${sizes[size]} ${className}`

  if (href) {
    return (
      <a
        href={href}
        className={cls}
        {...(external ? { target: '_blank', rel: 'noopener' } : {})}
        {...props}
      >
        {children}
      </a>
    )
  }
  return (
    <button className={cls} {...props}>
      {children}
    </button>
  )
}
