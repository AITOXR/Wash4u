# Wash4You — React landing site

Modern, conversion-focused single-page site for wash4you.in.
Vite + React + Tailwind CSS v4 + Framer Motion.

## Commands

```bash
npm install        # once
npm run dev        # local dev server (hot reload)
npm run build      # production build → dist/
npm run preview    # preview the production build
```

## Editing content

All copy, prices, service areas, FAQs, and contact details live in
`src/content.js` — edit there, components update automatically.

- Pricing came from the client's rate list (GST extra).
- Testimonials are the customer quotes from the existing wash4you.in site.
- The area checker treats any 122xxx pincode as Gurugram and matches the
  8 listed service areas by name; everything else routes to WhatsApp.

## Structure

```
src/
├── content.js            # ALL site content
├── App.jsx               # section order
├── components/ui/        # Button, Card, SectionHeading, Reveal, Stars, Icon
└── sections/             # Navbar, Hero, HowItWorks, Services, Pricing,
                          # AreaChecker, WhyUs, Testimonials, BookingCTA,
                          # FAQ, Footer
```

## QA tip

Append `?noanim` to the URL to disable scroll-reveal animations
(useful for full-page screenshots).

## Deploying

`dist/` is fully static — deployable to GitHub Pages, Vercel, or Netlify.
Asset paths are relative (`base: './'`), so it works from any subpath.
