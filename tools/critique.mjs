/* Capture every distinct page TYPE plus interaction states, for visual review. */
import puppeteer from 'puppeteer-core'
import { mkdir } from 'node:fs/promises'
const OUT = process.argv[2]
await mkdir(OUT, { recursive: true })
const B = 'http://127.0.0.1:8099'
const b = await puppeteer.launch({ executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:'new', args:['--no-sandbox','--font-render-hinting=none'] })

const TYPES = [
  ['home','/'],
  ['services-index','/services/'],
  ['service-proof','/services/shoe-cleaning/'],
  ['service-noproof','/services/toy-cleaning/'],
  ['locality','/laundry-service-sushant-lok/'],
  ['matrix','/shoe-cleaning-cyber-city/'],
  ['pricing','/pricing/'],
  ['about','/about-us/'],
  ['contact','/contact-us/'],
  ['locate','/locate-us/'],
  ['blog','/blog/'],
  ['policy','/terms-and-conditions/'],
  ['steam','/steam-iron/'],
  ['notfound','/404.html'],
]

const shoot = async (page, name, vp) => {
  const H = await page.evaluate(()=>document.documentElement.scrollHeight)
  const chunks=[]
  for(let y=0;y<H;y+=vp.height){
    const at = await page.evaluate(t=>{window.scrollTo(0,t);return window.scrollY}, y)
    await new Promise(r=>setTimeout(r,180))
    chunks.push({y:at, buf: await page.screenshot({encoding:'base64'})})
    if(at+vp.height>=H) break
  }
  return {H, chunks}
}

const fs = await import('node:fs/promises')
for (const vp of [{n:'d',width:1440,height:900,m:false},{n:'m',width:390,height:844,m:true}]) {
  for (const [name,path] of TYPES) {
    const p = await b.newPage()
    await p.setViewport({width:vp.width,height:vp.height,isMobile:vp.m,hasTouch:vp.m,deviceScaleFactor:1})
    await p.goto(B+path,{waitUntil:'networkidle0'})
    await p.evaluate(async()=>{const s=innerHeight*0.6;for(let y=0;y<document.body.scrollHeight;y+=s){scrollTo(0,y);await new Promise(r=>setTimeout(r,60))}scrollTo(0,0)})
    await new Promise(r=>setTimeout(r,1800))
    const {H,chunks} = await shoot(p,name,vp)
    for(let i=0;i<chunks.length;i++) await fs.writeFile(`${OUT}/${name}-${vp.n}-${String(i).padStart(2,'0')}.png`, Buffer.from(chunks[i].buf,'base64'))
    await fs.writeFile(`${OUT}/${name}-${vp.n}.json`, JSON.stringify({height:H, offsets:chunks.map(c=>c.y), width:vp.width}))
    await p.close()
  }
}
await b.close()
console.log('captured')
