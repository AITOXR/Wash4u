/* Render the print-only price list to a real PDF.

   Reads dist/pricing-print.html (build it first: python3 src/build.py) from the
   local preview server, prints it to A4, and writes the PDF to BOTH
   src/assets/ (committed, so the next build copies it) and dist/assets/ (so the
   running preview serves it immediately).

   Usage:  python3 src/build.py && (serve dist on :8099) && node tools/make-pdf.mjs
*/
import puppeteer from 'puppeteer-core'
import { copyFile, mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const BASE = process.argv[2] || 'http://127.0.0.1:8099'
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const SRC = resolve(ROOT, 'src/assets/wash4you-price-list.pdf')
const DIST = resolve(ROOT, 'dist/assets/wash4you-price-list.pdf')

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: 'new', args: ['--no-sandbox'],
})
const page = await browser.newPage()
const resp = await page.goto(`${BASE}/pricing-print.html`, { waitUntil: 'networkidle0' })
if (!resp || !resp.ok()) {
  console.error(`Could not load ${BASE}/pricing-print.html (status ${resp && resp.status()}). Build the site and start the server first.`)
  await browser.close()
  process.exit(1)
}
// Ensure webfonts are in before printing.
await page.evaluateHandle('document.fonts.ready')

await mkdir(dirname(SRC), { recursive: true })
await page.pdf({
  path: SRC,
  format: 'A4',
  printBackground: true,
  preferCSSPageSize: true,
})
await browser.close()

await mkdir(dirname(DIST), { recursive: true }).catch(() => {})
await copyFile(SRC, DIST).catch((e) => console.warn('dist copy skipped:', e.message))

console.log(`Wrote ${SRC}`)
console.log(`Wrote ${DIST}`)
