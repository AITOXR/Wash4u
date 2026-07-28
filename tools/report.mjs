/* Turn audit JSON into a per-page table + summary. */
import { readFile } from 'node:fs/promises'

const files = process.argv.slice(2)
const sets = {}
for (const f of files) {
  const data = JSON.parse(await readFile(f, 'utf8'))
  sets[data[0]?.viewport || f] = data
}

const EXPECTED = ['Archivo', 'Figtree', 'IBM Plex Mono']
const verdict = r => {
  const p = []
  if (r.error) return { ok: false, notes: ['LOAD ERROR: ' + r.error] }
  if (r.imgBroken?.length) p.push(`img broken: ${r.imgBroken.join(',')}`)
  if (r.imgNoAlt?.length) p.push(`img no-alt: ${r.imgNoAlt.length}`)
  if (r.fontUnexpected?.length) p.push(`font: ${r.fontUnexpected.join(',')}`)
  if (r.fontsLoaded?.length !== EXPECTED.length) p.push(`webfont not loaded: ${EXPECTED.filter(f=>!r.fontsLoaded?.includes(f)).join(',')}`)
  if (r.h1Count !== 1) p.push(`h1=${r.h1Count}`)
  if (r.emptyHeadings) p.push(`empty headings: ${r.emptyHeadings}`)
  if (r.artifacts?.length) p.push(`text: ${r.artifacts.join(',')}`)
  if (r.headingSkips) p.push(`heading skips: ${r.headingSkips}`)
  if (r.overflow?.length) p.push(`overflow: ${r.overflow.join(',')}`)
  if (r.smallTargets?.length) p.push(`tap<44: ${r.smallTargets.join(',')}`)
  if (r.stillHidden) p.push(`hidden after scroll: ${r.stillHidden}`)
  if (r.stranded) p.push(`stranded transform: ${r.stranded}`)
  if (r.consoleErrors?.length) p.push(`js: ${r.consoleErrors[0].slice(0,60)}`)
  if (r.httpBad?.length) p.push(`http: ${r.httpBad.join(',')}`)
  if (r.titleLen > 65) p.push(`title ${r.titleLen}ch`)
  if (!r.metaDesc) p.push('no meta description')
  if (!r.canonical) p.push('no canonical')
  return { ok: p.length === 0, notes: p }
}

const group = p => {
  if (p === '/') return 'Home'
  if (p.startsWith('/services/') && p !== '/services/') return 'Service'
  if (p === '/services/') return 'Services index'
  if (p.startsWith('/laundry-service-')) return 'Locality'
  if (/^\/(terms|privacy|refund|curtain|free-pickup)/.test(p)) return 'Policy'
  if (/^\/(about-us|contact-us|pricing|blog|locate-us|steam-iron|404)/.test(p)) return 'Core'
  return 'Service×Locality'
}

for (const [vp, data] of Object.entries(sets)) {
  const rows = data.map(r => ({ ...r, ...verdict(r), group: group(r.path) }))
  const fails = rows.filter(r => !r.ok)
  console.log(`\n## ${vp.toUpperCase()} — ${rows.length} pages, ${fails.length} with findings\n`)

  const byGroup = {}
  for (const r of rows) { (byGroup[r.group] ||= []).push(r) }
  console.log('| Group | Pages | Clean | Imgs/page | Fonts OK | Motion OK | Findings |')
  console.log('|---|---|---|---|---|---|---|')
  for (const [g, rs] of Object.entries(byGroup)) {
    const clean = rs.filter(r => r.ok).length
    const imgs = (rs.reduce((a, r) => a + (r.imgTotal || 0), 0) / rs.length).toFixed(1)
    const fonts = rs.filter(r => !r.fontUnexpected?.length && r.fontsLoaded?.length === 3).length
    const motion = rs.filter(r => !r.stillHidden && !r.stranded).length
    console.log(`| ${g} | ${rs.length} | ${clean}/${rs.length} | ${imgs} | ${fonts}/${rs.length} | ${motion}/${rs.length} | ${rs.length - clean} |`)
  }

  if (fails.length) {
    console.log(`\n### Findings (${vp})\n`)
    console.log('| URL | Finding |'); console.log('|---|---|')
    for (const r of fails.slice(0, 40)) console.log(`| \`${r.path}\` | ${r.notes.join('; ')} |`)
    if (fails.length > 40) console.log(`| … | ${fails.length - 40} more |`)
  }

  // aggregates
  const allFams = new Set(); rows.forEach(r => (r.families || []).forEach(f => allFams.add(f)))
  console.log(`\n**Font families rendered across all pages:** ${[...allFams].join(', ')}`)
  console.log(`**Total images checked:** ${rows.reduce((a, r) => a + (r.imgTotal || 0), 0)}  |  **broken:** ${rows.reduce((a, r) => a + (r.imgBroken?.length || 0), 0)}`)
  console.log(`**Pages with 0 console errors:** ${rows.filter(r => !r.consoleErrors?.length).length}/${rows.length}`)
  console.log(`**Word count:** min ${Math.min(...rows.map(r => r.wordCount || 0))}, median ${rows.map(r => r.wordCount || 0).sort((a, b) => a - b)[Math.floor(rows.length / 2)]}, max ${Math.max(...rows.map(r => r.wordCount || 0))}`)
}
