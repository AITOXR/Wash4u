/* Focused QA for the client-feedback pass: cart flow, mega-menu, tap targets,
   and screenshots of every new surface at desktop + mobile. */
import puppeteer from 'puppeteer-core'
import { mkdir } from 'node:fs/promises'

const OUT = process.argv[2]
await mkdir(OUT, { recursive: true })
const B = 'http://127.0.0.1:8099'
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const b = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--font-render-hinting=none'] })
const log = []
const ok = (name, pass, detail = '') => log.push([pass ? 'PASS' : 'FAIL', name, detail])

const settle = (p, ms = 900) => p.evaluate(async () => {
  const s = innerHeight * 0.6
  for (let y = 0; y < document.body.scrollHeight; y += s) { scrollTo(0, y); await new Promise(r => setTimeout(r, 50)) }
  scrollTo(0, 0)
}).then(() => new Promise(r => setTimeout(r, ms)))

const errsOf = (p) => { const e = []; p.on('pageerror', x => e.push(String(x))); p.on('console', m => { if (m.type() === 'error') e.push(m.text()) }); return e }

/* ---- 1. Cart flow on /pricing/ (desktop) ---- */
{
  const p = await b.newPage(); await p.setViewport({ width: 1440, height: 900 })
  const errs = errsOf(p)
  await p.goto(B + '/pricing/', { waitUntil: 'networkidle0' }); await settle(p)
  // add first item twice, second item once
  const cards = await p.$$('[data-price-item]')
  const firstName = await p.evaluate(el => el.dataset.name, cards[0])
  await p.click('[data-price-item]:nth-of-type(1) [data-add]')
  await new Promise(r => setTimeout(r, 150))
  // after add, control becomes a stepper — click its inc
  await p.click('[data-price-item]:nth-of-type(1) [data-inc]')
  await new Promise(r => setTimeout(r, 150))
  await p.click('[data-price-item]:nth-of-type(2) [data-add]')
  await new Promise(r => setTimeout(r, 200))

  const badge = await p.$eval('#cart-toggle [data-cart-count]', el => el.textContent)
  ok('cart badge counts 3 after 2+1', badge === '3', `badge=${badge}`)
  const toggleShown = await p.$eval('#cart-toggle', el => !el.hidden)
  ok('cart toggle becomes visible', toggleShown)

  // open drawer
  await p.click('#cart-toggle'); await new Promise(r => setTimeout(r, 400))
  const open = await p.$eval('#cart-drawer', el => el.classList.contains('is-open') && el.getAttribute('aria-hidden') === 'false')
  ok('drawer opens', open)
  const lines = await p.$$eval('.cart-line', els => els.length)
  ok('drawer shows 2 distinct lines', lines === 2, `lines=${lines}`)
  const total = await p.$eval('[data-cart-total]', el => el.textContent)
  const href = await p.$eval('[data-cart-book]', el => el.getAttribute('href'))
  ok('book link is a wa.me url with prefilled text', /wa\.me\/916367600500\?text=/.test(href), href.slice(0, 60))
  ok('book link includes an item name', decodeURIComponent(href).includes(firstName), `first=${firstName}`)
  ok('book link mentions GST', /GST/.test(decodeURIComponent(href)))
  await p.screenshot({ path: `${OUT}/cart-drawer-desktop.png` })

  // persistence: reload keeps the cart
  await p.reload({ waitUntil: 'networkidle0' }); await new Promise(r => setTimeout(r, 400))
  const badge2 = await p.$eval('[data-cart-count]', el => el.textContent)
  ok('cart persists across reload (localStorage)', badge2 === '3', `badge2=${badge2}`)

  // tap-target sizes now >=44 for the always-present controls
  await p.click('#cart-toggle'); await new Promise(r => setTimeout(r, 300))
  const sizes = await p.evaluate(() => {
    const r = (s) => { const el = document.querySelector(s); if (!el) return null; const b = el.getBoundingClientRect(); return [Math.round(b.width), Math.round(b.height)] }
    return { close: r('.cart-drawer__close'), clear: r('.cart-drawer__clear'), add: r('.price-card__add'), qty: r('.qty__btn') }
  })
  ok('cart close >=44', sizes.close && sizes.close[1] >= 44, JSON.stringify(sizes.close))
  ok('cart clear >=44', sizes.clear && sizes.clear[1] >= 44, JSON.stringify(sizes.clear))
  ok('qty btn >=44', sizes.qty && sizes.qty[1] >= 44, JSON.stringify(sizes.qty))
  // clear it
  await p.click('[data-cart-clear]'); await new Promise(r => setTimeout(r, 200))
  const emptyBadge = await p.$eval('[data-cart-count]', el => el.textContent)
  ok('clear empties cart', emptyBadge === '0', `badge=${emptyBadge}`)
  ok('/pricing/ no console errors', errs.length === 0, errs.slice(0, 2).join(' | '))
  await p.close()
}

/* ---- 2. Add-button tap size on a fresh load (initial state) ---- */
{
  const p = await b.newPage(); await p.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true })
  await p.evaluateOnNewDocument(() => { try { localStorage.clear() } catch {} })
  await p.goto(B + '/pricing/', { waitUntil: 'networkidle0' }); await settle(p, 600)
  const add = await p.$eval('.price-card__add', el => { const b = el.getBoundingClientRect(); return Math.round(b.height) })
  ok('mobile add button >=44', add >= 44, `h=${add}`)
  await p.screenshot({ path: `${OUT}/pricing-mobile.png`, fullPage: false })
  await p.close()
}

/* ---- 3. Mega dropdown (desktop hover) ---- */
{
  const p = await b.newPage(); await p.setViewport({ width: 1440, height: 900 })
  await p.goto(B + '/', { waitUntil: 'networkidle0' }); await new Promise(r => setTimeout(r, 700))
  await p.hover('.has-dropdown .header__link--parent')
  await new Promise(r => setTimeout(r, 400))
  const megaVisible = await p.evaluate(() => {
    const m = document.querySelector('.has-dropdown .mega')
    if (!m) return false
    const cs = getComputedStyle(m)
    return cs.visibility === 'visible' && parseFloat(cs.opacity) > 0.9
  })
  ok('services mega opens on hover', megaVisible)
  const aria = await p.$eval('.has-dropdown .header__link--parent', el => el.getAttribute('aria-expanded'))
  ok('aria-expanded synced to true on hover', aria === 'true', `aria=${aria}`)
  await p.screenshot({ path: `${OUT}/mega-services-desktop.png`, clip: { x: 0, y: 0, width: 1440, height: 460 } })
  await p.close()
}

/* ---- 4. Screenshots of new surfaces ---- */
const shoot = async (path, name, vp) => {
  const p = await b.newPage(); await p.setViewport(vp)
  await p.goto(B + path, { waitUntil: 'networkidle0' }); await settle(p, 1000)
  await p.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
  await p.close()
}
const D = { width: 1440, height: 900 }, M = { width: 390, height: 844, isMobile: true, hasTouch: true }
await shoot('/', 'home-desktop', D)
await shoot('/', 'home-mobile', M)
await shoot('/packages/', 'packages-desktop', D)
await shoot('/pricing/sushant-lok/', 'pricing-area-desktop', D)

await b.close()

const pass = log.filter(l => l[0] === 'PASS').length
const fail = log.filter(l => l[0] === 'FAIL').length
console.log(`\n=== QA: ${pass} passed, ${fail} failed ===`)
for (const [s, n, d] of log) console.log(`  ${s}  ${n}${d ? '  — ' + d : ''}`)
process.exit(fail ? 1 : 0)
