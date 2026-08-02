/* Turn the supplied price-list poster into the downloadable PDF.
 *
 * The "Download PDF" button on /pricing/ used to serve a PDF printed from
 * dist/pricing-print.html (tools/make-pdf.mjs, still available as
 * `npm run build:pdf:generated`). The client now supplies a designed poster
 * that IS the price list, so that artwork is what people should get.
 *
 * No server needed: the page is a data: URI holding the image, printed at the
 * poster's own aspect ratio via @page, so the PDF is edge-to-edge artwork
 * rather than a portrait image letterboxed onto A4.
 *
 * Usage:  node tools/poster-pdf.mjs
 */
import puppeteer from 'puppeteer-core'
import { readFile, writeFile, copyFile, mkdir, access } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const POSTER = resolve(ROOT, 'src/assets/images/price-list-poster.jpg')
const SRC = resolve(ROOT, 'src/assets/wash4you-price-list.pdf')
const DIST = resolve(ROOT, 'dist/assets/wash4you-price-list.pdf')

const bytes = await readFile(POSTER)
const dataUri = `data:image/jpeg;base64,${bytes.toString('base64')}`

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: 'new', args: ['--no-sandbox'],
})
const page = await browser.newPage()

// Measure the poster so the page box matches it exactly.
await page.setContent(`<img id="p" src="${dataUri}">`)
const { w, h } = await page.evaluate(() => {
  const i = document.getElementById('p')
  return { w: i.naturalWidth, h: i.naturalHeight }
})

// 96 CSS px = 1in is the PDF unit Chrome prints at.
const wIn = (w / 96).toFixed(4)
const hIn = (h / 96).toFixed(4)

await page.setContent(
  `<style>
     @page { size: ${wIn}in ${hIn}in; margin: 0; }
     html, body { margin: 0; padding: 0; }
     img { display: block; width: 100%; height: auto; }
   </style>
   <img src="${dataUri}">`,
  { waitUntil: 'load' }
)

await mkdir(dirname(SRC), { recursive: true })
await page.pdf({ path: SRC, printBackground: true, preferCSSPageSize: true })
await browser.close()

// dist/ may not exist yet if the site has not been built in this checkout.
try {
  await access(dirname(DIST))
  await copyFile(SRC, DIST)
} catch {
  /* no dist yet — the next `npm run build` copies src/assets across */
}

console.log(`Price-list PDF written from the poster (${w}x${h}px -> ${wIn}x${hIn}in).`)
