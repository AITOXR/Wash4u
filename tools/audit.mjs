/* Full-site audit: text, fonts, UI/UX, motion, images — every page.
   Usage: node tools/audit.mjs <baseUrl> <out.json> [viewport]
*/
import puppeteer from 'puppeteer-core'
import { writeFile, readFile } from 'node:fs/promises'

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const base = process.argv[2] || 'http://127.0.0.1:8099'
const outFile = process.argv[3] || 'audit.json'
const vpName = process.argv[4] || 'mobile'
const VP = vpName === 'desktop'
  ? { width: 1440, height: 900, isMobile: false }
  : { width: 390, height: 844, isMobile: true }

// every URL, straight from the generated sitemap
const sitemap = await readFile('dist/sitemap.xml', 'utf8')
const paths = [...sitemap.matchAll(/<loc>https:\/\/wash4you\.in(\/[^<]*)<\/loc>/g)].map(m => m[1])

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: 'new',
  args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
})

const EXPECTED_FONTS = ['Archivo', 'Figtree', 'IBM Plex Mono']
const results = []

for (const path of paths) {
  const page = await browser.newPage()
  await page.setViewport({ ...VP, deviceScaleFactor: 1, hasTouch: VP.isMobile })

  const consoleErrors = []
  const httpBad = []
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()) })
  page.on('pageerror', e => consoleErrors.push(String(e)))
  page.on('response', r => { if (!r.ok() && r.status() !== 304) httpBad.push(`${r.status()} ${r.url().replace(base, '')}`) })
  page.on('requestfailed', r => httpBad.push(`FAIL ${r.url().replace(base, '')}`))

  let rec
  try {
    await page.goto(base + path, { waitUntil: 'networkidle0', timeout: 30000 })

    // scroll through so reveals fire and lazy images request
    await page.evaluate(async () => {
      const step = window.innerHeight * 0.6
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y); await new Promise(r => setTimeout(r, 70))
      }
      window.scrollTo(0, document.body.scrollHeight)
      await new Promise(r => setTimeout(r, 2600))
    })

    rec = await page.evaluate(async (EXPECTED) => {
      const vw = window.innerWidth

      /* ---- IMAGES ----
         Force every lazy image to load rather than scrolling each into view:
         same assertion (does the src resolve and decode?) but seconds faster
         across 108 pages, and immune to a lazy image unloading again. */
      const all = [...document.images]
      all.forEach(i => { i.loading = 'eager' })
      await Promise.all(all.map(i => i.complete
        ? Promise.resolve()
        : new Promise(res => { i.addEventListener('load', res, { once: true }); i.addEventListener('error', res, { once: true }); setTimeout(res, 4000) })))
      const imgs = all.map(im => ({ src: (im.getAttribute('src') || '').split('/').slice(-1)[0], nw: im.naturalWidth, alt: im.getAttribute('alt') }))
      const imgBroken = imgs.filter(i => i.nw === 0).map(i => i.src)
      const imgNoAlt = imgs.filter(i => i.alt === null).map(i => i.src)

      /* ---- FONTS ---- */
      const famOf = el => (getComputedStyle(el).fontFamily.split(',')[0] || '').replace(/["']/g, '').trim()
      const seen = {}
      for (const el of document.querySelectorAll('h1,h2,h3,h4,p,li,a,button,span,td,th,label,blockquote,address,strong,em')) {
        if (!el.textContent.trim()) continue
        const f = famOf(el); if (!f) continue
        seen[f] = (seen[f] || 0) + 1
      }
      const families = Object.keys(seen)
      const fontUnexpected = families.filter(f => !EXPECTED.includes(f))
      const fontsLoaded = EXPECTED.filter(f => document.fonts.check(`400 1rem "${f}"`))
      // a heading rendering in the body face means the display face failed
      const h = document.querySelector('h1')
      const h1Family = h ? famOf(h) : null

      /* ---- TEXT ---- */
      const heads = [...document.querySelectorAll('h1,h2,h3,h4')]
      const emptyHeadings = heads.filter(x => !x.textContent.trim()).length
      const bodyText = document.body.innerText
      const artifacts = []
      if (/\*\*/.test(bodyText)) artifacts.push('** literal')
      if (/(^|\s)\*[A-Za-z][^*\n]{0,60}\*(\s|$)/.test(bodyText)) artifacts.push('* literal')
      if (/\bundefined\b|\[object Object\]|\{\{|\}\}/.test(bodyText)) artifacts.push('template leak')
      if (/Lorem ipsum/i.test(bodyText)) artifacts.push('lorem')
      // heading level skips
      let prev = 0, skips = 0
      for (const x of heads) { const lv = +x.tagName[1]; if (prev && lv > prev + 1) skips++; prev = lv }

      /* ---- UI / UX ---- */
      const inScroller = el => {
        for (let p = el.parentElement; p; p = p.parentElement) {
          const ov = getComputedStyle(p).overflowX
          if (ov === 'auto' || ov === 'scroll' || ov === 'hidden') return true
        } return false
      }
      const overflow = []
      for (const el of document.querySelectorAll('body *')) {
        const r = el.getBoundingClientRect()
        if (r.width === 0) continue
        if ((r.right > vw + 1 || r.left < -1) && !inScroller(el)) overflow.push(el.tagName.toLowerCase() + '.' + String(el.className).split(' ')[0])
      }
      // real tap targets only: exclude inline text links inside prose/nav lists
      const smallTargets = []
      for (const el of document.querySelectorAll('button, a.btn, .rail-nav button, .menu-toggle, input, select, textarea')) {
        const r = el.getBoundingClientRect()
        if (!r.width || !r.height) continue
        if (r.height < 44 || r.width < 44) smallTargets.push(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} ${Math.round(r.width)}x${Math.round(r.height)}`)
      }

      /* ---- MOTION ---- */
      const hooks = [...document.querySelectorAll('.reveal, .stagger-children > *')].filter(e => { const b = e.getBoundingClientRect(); return b.width || b.height })
      const stillHidden = hooks.filter(e => parseFloat(getComputedStyle(e).opacity) < 0.99).length
      const stranded = hooks.filter(e => { const t = getComputedStyle(e).transform; return t !== 'none' && t !== 'matrix(1, 0, 0, 1, 0, 0)' }).length

      /* ---- LINKS ---- */
      const internal = [...document.querySelectorAll('a[href]')]
        .map(a => a.getAttribute('href'))
        .filter(h => h && !/^(https?:|tel:|mailto:|#)/.test(h))

      return {
        title: document.title, titleLen: document.title.length,
        metaDesc: (document.querySelector('meta[name=description]') || {}).content || '',
        canonical: (document.querySelector('link[rel=canonical]') || {}).href || '',
        imgTotal: imgs.length, imgBroken, imgNoAlt,
        families, fontUnexpected, fontsLoaded, h1Family,
        h1Count: document.querySelectorAll('h1').length,
        emptyHeadings, artifacts, headingSkips: skips,
        overflow: [...new Set(overflow)].slice(0, 5),
        smallTargets: [...new Set(smallTargets)].slice(0, 5),
        stillHidden, stranded,
        wordCount: bodyText.trim().split(/\s+/).length,
        internalLinks: [...new Set(internal)],
      }
    }, EXPECTED_FONTS)
  } catch (e) {
    rec = { error: String(e).slice(0, 160) }
  }

  results.push({ path, viewport: vpName, consoleErrors: consoleErrors.slice(0, 3), httpBad: [...new Set(httpBad)].slice(0, 5), ...rec })
  await page.close()
  if (results.length % 20 === 0) console.error(`  ...${results.length}/${paths.length}`)
}

await browser.close()
await writeFile(outFile, JSON.stringify(results, null, 1))
console.error(`done: ${results.length} pages -> ${outFile}`)
