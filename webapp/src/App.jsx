import { MotionConfig } from 'framer-motion'
import Navbar from './sections/Navbar'
import Hero from './sections/Hero'
import HowItWorks from './sections/HowItWorks'
import Services from './sections/Services'
import Pricing from './sections/Pricing'
import AreaChecker from './sections/AreaChecker'
import WhyUs from './sections/WhyUs'
import Testimonials from './sections/Testimonials'
import BookingCTA from './sections/BookingCTA'
import FAQ from './sections/FAQ'
import Footer from './sections/Footer'

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <a
        href="#top"
        className="sr-only focus:not-sr-only focus:fixed focus:left-1/2 focus:top-3 focus:z-[100] focus:-translate-x-1/2 focus:rounded-lg focus:bg-teal focus:px-4 focus:py-2 focus:text-white"
      >
        Skip to content
      </a>
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <Services />
        <Pricing />
        <AreaChecker />
        <WhyUs />
        <Testimonials />
        <BookingCTA />
        <FAQ />
      </main>
      <Footer />
    </MotionConfig>
  )
}
