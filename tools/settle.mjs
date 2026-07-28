import puppeteer from 'puppeteer-core'
const b = await puppeteer.launch({ executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:'new', args:['--no-sandbox'] })
const urls = ['/services/sofa-cleaning/','/services/shoe-cleaning/','/services/premium-dry-cleaning/','/laundry-service-sushant-lok/','/laundry-service-gurugram-sector-29/','/laundry-service-palam-vihar/']
for (const vp of [{n:'mobile',w:390,h:844,m:true},{n:'desktop',w:1440,h:900,m:false}]) {
  for (const url of urls) {
    const p = await b.newPage(); await p.setViewport({width:vp.w,height:vp.h,isMobile:vp.m})
    await p.goto('http://127.0.0.1:8099'+url,{waitUntil:'networkidle0'})
    const snap = async () => p.evaluate(()=>{
      const all=[...document.querySelectorAll('.reveal, .stagger-children > *')].filter(e=>{const r=e.getBoundingClientRect();return r.width||r.height})
      return { hidden: all.filter(e=>parseFloat(getComputedStyle(e).opacity)<0.99).length,
               stranded: all.filter(e=>{const t=getComputedStyle(e).transform;return t!=='none'&&t!=='matrix(1, 0, 0, 1, 0, 0)'}).length,
               where: all.filter(e=>parseFloat(getComputedStyle(e).opacity)<0.99).slice(0,3).map(e=>e.tagName+'.'+String(e.className).split(' ')[0]) }
    })
    await p.evaluate(async()=>{const s=innerHeight*0.6;for(let y=0;y<document.body.scrollHeight;y+=s){scrollTo(0,y);await new Promise(r=>setTimeout(r,70))}scrollTo(0,document.body.scrollHeight)})
    await new Promise(r=>setTimeout(r,1200)); const at1200 = await snap()
    await new Promise(r=>setTimeout(r,2300)); const at3500 = await snap()
    const tag = at3500.hidden||at3500.stranded ? 'STUCK' : 'settles'
    console.log(`${vp.n.padEnd(8)} ${url.padEnd(38)} @1.2s h${at1200.hidden}/s${at1200.stranded}  @3.5s h${at3500.hidden}/s${at3500.stranded}  ${tag}`, at3500.hidden?at3500.where:'')
    await p.close()
  }
}
await b.close()
