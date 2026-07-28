/* Screenshot + layout audit against a locally served build.
   Uses the Chrome already installed on the machine (puppeteer-core does not
   download its own Chromium). macOS Chrome clamps a headless window to a
   500px minimum, so real phone widths need CDP device emulation — which is
   the whole reason this script exists.

   Usage:  node tools/shot.mjs <baseUrl> <outDir> [path ...]
*/
import puppeteer from 'puppeteer-core'
import { mkdir, writeFile } from 'node:fs/promises'

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

/* deviceScaleFactor stays at 1. A full-page capture of a long page at 2–3x
   exceeds Chrome's ~16384px texture limit and silently renders the overflow
   as blank white — which reads exactly like a broken layout. */
const VIEWPORTS = [
  { name: 'mobile',  width: 390,  height: 844,  dsf: 1, mobile: true },
  { name: 'tablet',  width: 834,  height: 1112, dsf: 1, mobile: true },
  { name: 'desktop', width: 1440, height: 900,  dsf: 1, mobile: false },
]

const base = process.argv[2] || 'http://127.0.0.1:8099'
const outDir = process.argv[3] || './shots'
const paths = process.argv.slice(4)
if (!paths.length) paths.push('/')

await mkdir(outDir, { recursive: true })

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
})

const report = []

for (const path of paths) {
  const slug = path.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'home'

  for (const vp of VIEWPORTS) {
    const page = await browser.newPage()
    const errors = []
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
    page.on('pageerror', (e) => errors.push(String(e)))

    await page.setViewport({
      width: vp.width,
      height: vp.height,
      deviceScaleFactor: vp.dsf,
      isMobile: vp.mobile,
      hasTouch: vp.mobile,
    })

    await page.goto(base + path, { waitUntil: 'networkidle0', timeout: 30000 })

    // Scroll the whole page once so scroll-triggered reveals and lazy images
    // have actually fired before we capture, then return to the top.
    await page.evaluate(async () => {
      const step = window.innerHeight * 0.8
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y)
        await new Promise((r) => setTimeout(r, 40))
      }
      window.scrollTo(0, 0)
      await new Promise((r) => setTimeout(r, 250))
    })

    // Audit: horizontal overflow, tap-target size, missing alt text.
    const audit = await page.evaluate(() => {
      const de = document.documentElement
      const vw = window.innerWidth

      // An element only counts as overflowing if no ancestor is a scroll
      // container — a wide card inside an overflow-x:auto rail is intended.
      const inScroller = (el) => {
        for (let p = el.parentElement; p; p = p.parentElement) {
          const ov = getComputedStyle(p).overflowX
          if (ov === 'auto' || ov === 'scroll' || ov === 'hidden') return true
        }
        return false
      }

      const overflow = []
      for (const el of document.querySelectorAll('body *')) {
        const r = el.getBoundingClientRect()
        if (r.width === 0) continue
        if ((r.right > vw + 1 || r.left < -1) && !inScroller(el)) {
          overflow.push(`${el.tagName.toLowerCase()}.${(el.className || '').toString().split(' ')[0]} [${Math.round(r.left)}..${Math.round(r.right)}]`)
        }
      }

      const smallTargets = []
      for (const el of document.querySelectorAll('a[href], button, input, select, textarea')) {
        const r = el.getBoundingClientRect()
        if (r.width === 0 || r.height === 0) continue
        if (getComputedStyle(el).position === 'absolute' && r.width < 4) continue
        if (r.height < 44 || r.width < 24) {
          smallTargets.push(`${el.tagName.toLowerCase()}."${(el.textContent || '').trim().slice(0, 28)}" ${Math.round(r.width)}x${Math.round(r.height)}`)
        }
      }

      const noAlt = [...document.querySelectorAll('img')]
        .filter((i) => i.getAttribute('alt') === null)
        .map((i) => i.getAttribute('src'))

      const h1s = [...document.querySelectorAll('h1')].map((h) => h.textContent.trim().slice(0, 60))

      return {
        vw,
        scrollWidth: de.scrollWidth,
        overflow: overflow.slice(0, 8),
        smallTargets: smallTargets.slice(0, 8),
        noAlt,
        h1Count: h1s.length,
        h1s,
        title: document.title,
      }
    })

    report.push({ path, viewport: vp.name, ...audit, errors: errors.slice(0, 5) })

    /* Capture by scrolling and stitching viewport-sized clips rather than
       using fullPage. A fullPage capture of this page renders everything past
       the first screen as blank — the sticky header's backdrop-filter creates
       a compositing layer that Chrome headless does not resolve correctly over
       a long capture. Clipped viewport shots composite normally. */
    const pageHeight = await page.evaluate(() => document.documentElement.scrollHeight)
    const chunks = []
    // A plain screenshot with no clip captures exactly the current viewport.
    // `clip` coordinates are page-relative, so passing y:0 per chunk would
    // re-capture the top of the page every time.
    for (let y = 0; y < pageHeight; y += vp.height) {
      const actual = await page.evaluate((top) => { window.scrollTo(0, top); return window.scrollY }, y)
      await new Promise((r) => setTimeout(r, 140))
      chunks.push({ y: actual, buf: await page.screenshot({ encoding: 'binary' }) })
      if (actual + vp.height >= pageHeight) break
    }
    await writeFile(`${outDir}/${slug}-${vp.name}.manifest.json`, JSON.stringify({ width: vp.width, height: pageHeight, offsets: chunks.map((c) => c.y) }))
    for (let i = 0; i < chunks.length; i++) {
      await writeFile(`${outDir}/${slug}-${vp.name}-${String(i).padStart(2, '0')}.png`, chunks[i].buf)
    }
    await page.close()
  }
}

await browser.close()
console.log(JSON.stringify(report, null, 1))
