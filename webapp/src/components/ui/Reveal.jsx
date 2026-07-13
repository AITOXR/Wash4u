import { motion } from 'framer-motion'

// Screenshot/QA escape hatch: ?noanim renders everything visible immediately.
const noAnim =
  typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('noanim')

// Fade/slide-in on scroll. Respects reduced motion via MotionConfig in App.
export default function Reveal({ children, delay = 0, y = 28, className = '' }) {
  if (noAnim) return <div className={className}>{children}</div>

  return (
    <motion.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-70px' }}
      transition={{ duration: 0.55, delay, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
