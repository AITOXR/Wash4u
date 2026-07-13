# Wash4You Website

A redesigned static website for **Wash4You** (`https://wash4you.in/`) inspired by the UI/UX of [Rinse.com](https://www.rinse.com/), with all original content preserved.

## Project Structure

```
.
├── src/                    # Source files (edit these)
│   ├── data/               # JSON content for all pages
│   ├── templates/          # Jinja2 HTML templates
│   ├── assets/             # CSS, JS, images
│   └── build.py            # Static site generator
├── dist/                   # Generated output (run build.py)
├── index.html              # Deployed homepage
├── ...                     # Deployed pages
└── README.md               # This file
```

## Quick Start

### Build the site

```bash
cd src
python3 build.py
```

This generates all pages into `dist/`.

### Preview locally

```bash
cd dist
python3 -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

### Deploy

The contents of `dist/` are copied to the project root for deployment. To update after editing source files:

```bash
cd src
python3 build.py
cd ..
rm -rf dist/*
cp -R dist/* .
```

## Editing Content

All page content lives in `src/data/` as JSON files:

- `site.json` — Brand info, navigation, footer, contact details, social links
- `home.json` — Hero, USPs, how-it-works, services, mission, testimonials, FAQs, CTA
- `about.json` — About page content
- `services.json` — Service list and detail content
- `pricing.json` — Pricing tables
- `steam-iron.json` — Steam iron page content
- `blog.json` — Blog listing
- `locations.json` — Locations and service-area pages
- `policies.json` — Policy pages (terms, privacy, refund, curtain, free pickup)
- `pages.json` — Contact form and 404 page

After editing JSON files, rebuild with `python3 build.py`.

## Design System

CSS is organized in `src/assets/css/`:

- `design-system.css` — Variables, reset, typography, utilities, buttons
- `components.css` — Header, footer, cards, forms, hero, testimonials, FAQ
- `pages.css` — Page-specific layouts
- `animations.css` — Scroll reveals and transitions

## Notes

- Built with Python and Jinja2 (no Node.js required).
- Uses Google Fonts: Bebas Neue (display) and Inter (body).
- All 34 original URLs preserved.
- External booking links point to `app.wash4you.in`.
